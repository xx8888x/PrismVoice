<?php

namespace App\Http\Controllers;

use App\Models\Article;
use App\Models\NewsEvent;
use App\Services\PerspectiveService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\Rule;

class NewsController extends Controller
{
    public function index(Request $request) {
        $demo = $request->boolean('demo');
        return NewsEvent::where('is_demo', $demo)->withCount('articles')->withMax('articles', 'published_at')->orderByDesc('articles_count')->orderByDesc('articles_max_published_at')->get();
    }
    public function show(NewsEvent $event) { return $event->load(['articles' => fn ($q) => $q->orderBy('published_at')->orderBy('id')]); }
    public function compare(Request $request, NewsEvent $event, PerspectiveService $service) {
        $data = $request->validate(['left' => ['required', 'integer'], 'right' => ['required', 'integer', 'different:left']]);
        $left = $event->articles()->findOrFail($data['left']); $right = $event->articles()->findOrFail($data['right']);
        return $service->compare($left->assessments, $right->assessments, $event->dimensions);
    }
    public function update(Request $request, Article $article) {
        $keys = array_column($article->newsEvent->dimensions, 'key');
        $rules = ['revision' => ['required', 'integer'], 'assessments' => ['required', 'array:'.implode(',', $keys)]];
        foreach ($keys as $key) {
            $rules["assessments.$key"] = ['required', 'array:score,confidence,evidence,actor,reason'];
            $rules["assessments.$key.score"] = ['present', 'nullable', 'integer', 'between:-2,2'];
            $rules["assessments.$key.confidence"] = ['required', 'numeric', 'between:0,1'];
            foreach (['evidence', 'actor', 'reason'] as $field) { $rules["assessments.$key.$field"] = ['present', 'nullable', 'string', 'max:1500']; }
        }
        $data = $request->validate($rules);
        foreach ($data['assessments'] as $key => &$assessment) {
            if ($assessment['score'] !== null && (empty(trim($assessment['evidence'] ?? '')) || empty(trim($assessment['actor'] ?? '')) || empty(trim($assessment['reason'] ?? '')))) {
                throw \Illuminate\Validation\ValidationException::withMessages(["assessments.$key.evidence" => '判定分數必須提供主張者、文字依據及理由。']);
            }
            $assessment['method'] = 'manual';
            if ($assessment['score'] === null) { $assessment['confidence'] = 0; }
        }
        unset($assessment);
        return DB::transaction(function () use ($article, $data) {
            $locked = Article::lockForUpdate()->findOrFail($article->id);
            abort_if($locked->revision !== $data['revision'], 409, '文章已更新，請重新載入再編輯。');
            $locked->update(['assessments' => $data['assessments'], 'analysis_status' => 'reviewed', 'revision' => $locked->revision + 1]);
            return $locked;
        });
    }
    public function move(Request $request, Article $article, PerspectiveService $service) {
        $data = $request->validate(['news_event_id' => ['required', 'integer', Rule::exists('news_events', 'id')->where('is_demo', $article->is_demo)], 'revision' => ['required', 'integer']]);
        return DB::transaction(function () use ($article, $data, $service) {
            $locked = Article::lockForUpdate()->findOrFail($article->id);
            abort_if($locked->revision !== $data['revision'], 409, '文章已更新，請重新載入。');
            if ($locked->news_event_id !== $data['news_event_id']) {
                $locked->update(['news_event_id' => $data['news_event_id'], 'assessments' => $service->assess($locked->title), 'analysis_status' => 'unreviewed', 'revision' => $locked->revision + 1]);
            }
            return $locked;
        });
    }
}
