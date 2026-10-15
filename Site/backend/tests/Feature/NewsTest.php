<?php

namespace Tests\Feature;

use App\Models\Article;
use App\Services\NewsImporter;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class NewsTest extends TestCase
{
    use RefreshDatabase;
    private function rows(): array { return [
        ['url' => 'https://udn.com/news/story/6656/1111111', 'title' => '黃之鋒案最新進展', 'published_at' => '2026-09-02T12:00:00+08:00'],
        ['url' => 'https://udn.com/news/story/6656/1111112', 'title' => '政院聲援黃之鋒', 'published_at' => '2026-09-01T12:00:00+08:00'],
        ['url' => 'https://udn.com/news/story/6656/1111113', 'title' => '不同事件的獨立新聞', 'published_at' => '2026-09-03T12:00:00+08:00'],
    ]; }
    public function test_import_is_idempotent_and_preserves_manual_annotations(): void {
        $importer = app(NewsImporter::class); $this->assertSame(3, $importer->import($this->rows())['created']);
        $article = Article::first(); $article->update(['analysis_status' => 'reviewed', 'revision' => 7]);
        $this->assertSame(3, $importer->import($this->rows())['skipped']);
        $this->assertSame(7, $article->fresh()->revision); $this->assertSame(3, Article::count());
    }
    public function test_timeline_is_chronological_and_comparison_cannot_cross_events(): void {
        app(NewsImporter::class)->import($this->rows()); $articles = Article::orderBy('id')->get();
        $this->getJson('/api/events/'.$articles[0]->news_event_id)->assertOk()->assertJsonPath('articles.0.id', $articles[1]->id);
        $this->getJson('/api/events/'.$articles[0]->news_event_id.'/compare?left='.$articles[0]->id.'&right='.$articles[2]->id)->assertNotFound();
        $this->getJson('/api/events/'.$articles[0]->news_event_id.'/compare?left='.$articles[0]->id.'&right='.$articles[0]->id)->assertUnprocessable();
    }
    public function test_annotation_validates_evidence_and_prevents_stale_overwrites(): void {
        app(NewsImporter::class)->import($this->rows()); $article = Article::first(); $assessments = $article->assessments;
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
        $this->seed(); app(NewsImporter::class)->import($this->rows());
        $demo = Article::where('is_demo', true)->first(); $real = Article::where('is_demo', false)->first();
        $other = Article::where('is_demo', false)->where('news_event_id', '!=', $real->news_event_id)->first();
        $this->getJson('/api/events?demo=1')->assertJsonCount(1)->assertJsonPath('0.is_demo', true);
        $this->patchJson('/api/articles/'.$real->id.'/event', ['news_event_id' => $demo->news_event_id, 'revision' => 1])->assertUnprocessable();
        $this->patchJson('/api/articles/'.$real->id.'/event', ['news_event_id' => $other->news_event_id, 'revision' => 1])->assertOk()->assertJsonPath('revision', 2)->assertJsonPath('assessments.position.score', null);
    }
    public function test_bad_urls_and_dates_are_rejected(): void {
        $this->assertSame(2, app(NewsImporter::class)->import([
            ['url' => 'http://127.0.0.1/admin', 'title' => 'bad', 'published_at' => '2026-09-01'],
            ['url' => 'https://udn.com/news/story/6656/123', 'title' => 'bad', 'published_at' => 'nonsense'],
        ])['invalid']);
    }
}
