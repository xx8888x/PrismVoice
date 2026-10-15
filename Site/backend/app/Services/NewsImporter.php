<?php

namespace App\Services;

use App\Models\Article;
use App\Models\NewsEvent;
use Carbon\CarbonImmutable;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;

class NewsImporter
{
    public function fetch(int $limit): array
    {
        $response = Http::timeout(25)->withUserAgent('Mediawebsites/1.0 (local RSS reader)')->get('https://udn.com/news/rssfeed/6638')->throw();
        $previous = libxml_use_internal_errors(true);
        try { $xml = simplexml_load_string($response->body(), \SimpleXMLElement::class, LIBXML_NONET); }
        finally { libxml_clear_errors(); libxml_use_internal_errors($previous); }
        if ($xml === false) { throw new \RuntimeException('RSS 格式無法解析'); }
        $rows = [];
        foreach ($xml->channel->item as $item) {
            $url = (string) $item->link;
            if (!preg_match('~/news/story/(6656|6657|10930)/~', $url)) { continue; }
            $rows[] = ['title' => (string) $item->title, 'url' => $url, 'published_at' => (string) $item->pubDate, 'source' => '聯合新聞網', 'author' => (string) $item->author, 'category' => (string) $item->category, 'imported_at' => now()->toIso8601String()];
            if (count($rows) >= $limit) { break; }
        }
        return $rows;
    }

    public function import(array $rows): array
    {
        $counts = ['created' => 0, 'skipped' => 0, 'invalid' => 0];
        foreach ($rows as $row) {
            $url = $row['url'] ?? ''; $title = trim($row['title'] ?? '');
            if (!preg_match('~^https://udn\.com/news/story/\d+/\d+$~', $url) || !$title || mb_strlen($title) > 1000 || empty($row['published_at'])) { $counts['invalid']++; continue; }
            try { $published = CarbonImmutable::parse($row['published_at'])->utc(); }
            catch (\Throwable) { $counts['invalid']++; continue; }
            if (Article::where('url_hash', hash('sha256', $url))->exists()) { $counts['skipped']++; continue; }
            DB::transaction(function () use ($row, $title, $url, $published, &$counts) {
                [$key, $label, $question] = $this->cluster($title, $url);
                // A topic rule is only a grouping suggestion; restrict to a rolling 14-day window.
                $event = NewsEvent::where('cluster_key', 'like', $key.':%')->whereHas('articles', fn ($q) => $q->whereBetween('published_at', [$published->subDays(14), $published->addDays(14)]))->latest('id')->first();
                $event ??= NewsEvent::firstOrCreate(['cluster_key' => $key.':'.$published->format('Y-m-d')], ['title' => $label, 'description' => '依標題中特定人物與議題暫時分組；可人工移動文章修正。時間軸使用報導發布時間，不等同事件發生時間。', 'dimensions' => PerspectiveService::dimensions($question)]);
                Article::create(['news_event_id' => $event->id, 'url' => $url, 'url_hash' => hash('sha256', $url), 'title' => $title, 'source' => '聯合新聞網', 'author' => mb_substr($row['author'] ?? '', 0, 255), 'category' => mb_substr($row['category'] ?? '', 0, 255), 'published_at' => $published, 'imported_at' => now(), 'assessments' => app(PerspectiveService::class)->assess($title)]);
                $counts['created']++;
            });
        }
        return $counts;
    }

    private function cluster(string $title, string $url): array
    {
        $rules = [
            ['student', '蔣得立入學與身分爭議', '/蔣得立|僑生|大寶|三寶/u', '是否支持進一步釐清入學程序與身分？'],
            ['city-debate', '陳其邁政績與跨市政治交鋒', '/(蔣萬安.*陳其邁|陳其邁.*蔣萬安|推銷高雄)/u', '如何評價陳其邁的高雄施政？'],
            ['chen-career', '陳其邁卸任與未來動向', '/陳其邁|麥克風/u', '是否肯定陳其邁卸任後承擔更大職責？'],
            ['wong', '黃之鋒司法處境與台灣聲援', '/黃之鋒/u', '是否支持釋放黃之鋒等民主人士？'],
            ['taichung-energy', '中火燃氣機組都審爭議', '/中火.*燃氣/u', '是否支持推進中火燃氣機組審查？'],
        ];
        foreach ($rules as [$key, $label, $pattern, $question]) { if (preg_match($pattern, $title)) { return [$key, $label, $question]; } }
        return ['single-'.substr(hash('sha256', $url), 0, 20), mb_substr($title, 0, 70), '對這則事件的核心措施持何種態度？'];
    }
}
