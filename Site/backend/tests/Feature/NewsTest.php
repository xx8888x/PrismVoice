<?php

namespace Tests\Feature;

use App\Models\Article;
use App\Models\ArticleContent;
use App\Models\NewsEvent;
use App\Models\Source;
use App\Services\PerspectiveService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

// Ingestion (dedup, URL/date validation, clustering) lives in python_service and is tested there.
class NewsTest extends TestCase
{
    use RefreshDatabase;
    private function event(string $title, bool $demo = false): NewsEvent {
        return NewsEvent::create(['cluster_key' => 'test-'.md5($title), 'title' => $title, 'description' => '測試', 'dimensions' => PerspectiveService::dimensions(), 'is_demo' => $demo]);
    }
    private function article(NewsEvent $event, string $title, string $published): Article {
        $url = 'https://news.example.test/'.md5($title);
        return Article::create(['news_event_id' => $event->id, 'url' => $url, 'url_hash' => hash('sha256', $url), 'title' => $title, 'source' => '測試來源', 'published_at' => $published, 'imported_at' => now(), 'assessments' => app(PerspectiveService::class)->assess($title), 'is_demo' => $event->is_demo]);
    }
    /** @return Article[] two articles in one event (newer first) plus one in another event */
    private function articles(): array {
        $wong = $this->event('黃之鋒司法處境');
        return [$this->article($wong, '黃之鋒案最新進展', '2026-09-02 04:00:00'), $this->article($wong, '政院聲援黃之鋒', '2026-09-01 04:00:00'), $this->article($this->event('其他事件'), '不同事件的獨立新聞', '2026-09-03 04:00:00')];
    }
    public function test_timeline_is_chronological_and_comparison_cannot_cross_events(): void {
        $articles = $this->articles();
        $this->getJson('/api/events/'.$articles[0]->news_event_id)->assertOk()->assertJsonPath('articles.0.id', $articles[1]->id);
        $this->getJson('/api/events/'.$articles[0]->news_event_id.'/compare?left='.$articles[0]->id.'&right='.$articles[2]->id)->assertNotFound();
        $this->getJson('/api/events/'.$articles[0]->news_event_id.'/compare?left='.$articles[0]->id.'&right='.$articles[0]->id)->assertUnprocessable();
        $this->getJson('/api/events/'.$articles[0]->news_event_id.'/compare?left='.$articles[0]->id.'&right='.$articles[1]->id)->assertOk()->assertJsonPath('status', 'undetermined');
    }
    public function test_annotation_validates_evidence_and_prevents_stale_overwrites(): void {
        $article = $this->articles()[0]; $assessments = $article->assessments;
        foreach ($assessments as &$assessment) { unset($assessment['method']); }
        unset($assessment);
        $assessments['position'] = ['score' => 2, 'confidence' => .9, 'actor' => '', 'evidence' => '', 'reason' => ''];
        $this->patchJson('/api/articles/'.$article->id, ['revision' => 1, 'assessments' => $assessments])->assertUnprocessable();
        $assessments['position'] = ['score' => 2, 'confidence' => .9, 'actor' => '受訪者', 'evidence' => '支持釋放', 'reason' => '直接支持事件核心主張'];
        $payload = ['revision' => 1, 'assessments' => $assessments];
        $this->patchJson('/api/articles/'.$article->id, $payload)->assertOk()->assertJsonPath('revision', 2)->assertJsonPath('assessments.position.method', 'manual');
        $this->patchJson('/api/articles/'.$article->id, $payload)->assertConflict();
    }
    public function test_demo_is_separate_and_moving_resets_event_specific_annotations(): void {
        $this->seed(); [$real, , $other] = $this->articles();
        $demo = Article::where('is_demo', true)->first();
        $this->getJson('/api/events?demo=1')->assertJsonCount(1)->assertJsonPath('0.is_demo', true);
        $this->patchJson('/api/articles/'.$real->id.'/event', ['news_event_id' => $demo->news_event_id, 'revision' => 1])->assertUnprocessable();
        $this->patchJson('/api/articles/'.$real->id.'/event', ['news_event_id' => $other->news_event_id, 'revision' => 1])->assertOk()->assertJsonPath('revision', 2)->assertJsonPath('assessments.position.score', null);
    }
    public function test_full_text_is_stored_but_never_served(): void {
        $article = $this->articles()[0];
        ArticleContent::create(['article_id' => $article->id, 'status' => 'ok', 'body' => '全文僅供內部分析', 'char_count' => 8, 'fetched_at' => now()]);
        $this->assertSame('全文僅供內部分析', $article->content->body);
        $this->assertArrayNotHasKey('body', $article->content->toArray());
        $response = $this->getJson('/api/events/'.$article->news_event_id)->assertOk();
        $this->assertStringNotContainsString('全文僅供內部分析', $response->getContent());
    }
    public function test_event_marks_reprints_with_their_original(): void {
        [$reprint, $original] = $this->articles();
        $reprint->update(['duplicate_of_article_id' => $original->id]);
        $this->getJson('/api/events/'.$original->news_event_id)->assertOk()
            ->assertJsonPath('articles.0.duplicate_of_article_id', null)
            ->assertJsonPath('articles.1.duplicate_of_article_id', $original->id);
        $this->assertTrue($reprint->duplicateOf->is($original));
        $original->delete();
        $this->assertNull($reprint->fresh()->duplicate_of_article_id);
    }
    public function test_seeded_sources_are_usable_by_the_pipeline(): void {
        $sources = Source::all();
        $this->assertGreaterThanOrEqual(10, $sources->where('is_active', true)->count());
        foreach ($sources as $source) {
            $this->assertNotFalse(@preg_match('~'.$source->link_pattern.'~', ''), $source->slug.' link_pattern');
            $this->assertStringStartsWith('https://', $source->feed_url);
        }
        $this->assertSame(['^/(\d+)', 'https://www.storm.mg/article/\1'], Source::where('slug', 'storm')->first()->link_rewrite);
        $this->assertSame(480, Source::where('slug', 'yahoo')->first()->pubdate_offset_minutes);
        $this->assertSame(0, Source::where('slug', 'cna')->first()->pubdate_offset_minutes);
        $this->assertStringContainsString(':not(.read-more-vendor)', Source::where('slug', 'yahoo')->first()->content_selector);
    }
}
