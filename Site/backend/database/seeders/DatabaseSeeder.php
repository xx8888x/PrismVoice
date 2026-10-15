<?php

namespace Database\Seeders;

use App\Models\Article;
use App\Models\NewsEvent;
use App\Services\PerspectiveService;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    public function run(): void {
        $event = NewsEvent::firstOrCreate(['cluster_key' => 'demo-transit'], ['title' => '示範：市中心汽車通行費提案', 'description' => '此事件與三篇文章均為虛構教學資料，用於示範相反主張如何在同一維度被識別，並非真實新聞。', 'dimensions' => PerspectiveService::dimensions('是否支持向進入市中心的汽車收取通行費？'), 'is_demo' => true]);
        $rows = [
            ['a', '示範｜交通研究者支持通行費：收入應投入公共運輸', '示範文章 A', '2026-09-01 01:00:00', 2, 2, 1, '交通研究者（虛構）', '支持收取通行費，將收入投入公共運輸。', '明確支持同一項通行費提案。'],
            ['b', '示範｜商圈代表反對通行費：替代運輸尚未到位', '示範文章 B', '2026-09-02 03:30:00', -2, 2, -1, '商圈代表（虛構）', '反對目前收取通行費，替代運輸尚未到位。', '明確反對目前實施同一項提案。'],
            ['c', '示範｜市府提出分階段試辦，邀雙方協商配套', '示範文章 C', '2026-09-03 06:00:00', 1, 2, 2, '市府代表（虛構）', '支持分階段試辦，邀雙方協商配套。', '有條件支持並提出配套。'],
        ];
        foreach ($rows as [$key, $title, $source, $time, $position, $focus, $tone, $actor, $evidence, $reason]) {
            $assessments = [];
            foreach (['position' => $position, 'focus' => $focus, 'tone' => $tone] as $dimension => $score) {
                $assessments[$dimension] = ['score' => $score, 'confidence' => 1, 'actor' => $actor, 'evidence' => $evidence, 'reason' => $dimension === 'position' ? $reason : '教學案例預設標註，展示不同維度可同時存在。', 'method' => 'demo'];
            }
            Article::firstOrCreate(['url_hash' => hash('sha256', 'demo:'.$key)], ['news_event_id' => $event->id, 'url' => null, 'title' => $title, 'source' => $source, 'author' => '虛構教學資料', 'published_at' => $time, 'imported_at' => now(), 'assessments' => $assessments, 'analysis_status' => 'reviewed', 'is_demo' => true]);
        }
    }
}
