<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void {
        // One row per feed. The Python pipeline reads active rows and writes the fetch health columns back.
        // No political-lean column on purpose: a source's spectrum position must be measured from its articles, not pre-labelled.
        Schema::create('sources', function (Blueprint $table) {
            $table->id(); $table->string('slug', 50)->unique(); $table->string('name');
            $table->string('homepage_url', 500); $table->string('feed_url', 1000);
            $table->string('media_type', 50); $table->string('owner')->nullable();
            $table->string('link_pattern', 500)->comment('Python regex an article URL must match; filters feed sections and rejects foreign hosts');
            $table->json('link_rewrite')->nullable()->comment('[pattern, replacement] applied before link_pattern, for feeds with relative or broken links');
            $table->string('content_selector')->nullable()->comment('CSS selector for the article body; empty = paragraph-density heuristic');
            $table->boolean('is_active')->default(true); $table->unsignedSmallInteger('fetch_interval_minutes')->default(30);
            $table->unsignedSmallInteger('max_items_per_fetch')->default(15);
            $table->dateTime('last_fetched_at')->nullable(); $table->dateTime('last_success_at')->nullable();
            $table->unsignedSmallInteger('consecutive_failures')->default(0); $table->text('last_error')->nullable();
            $table->timestamps();
        });
        Schema::table('articles', function (Blueprint $table) {
            $table->foreignId('source_id')->nullable()->after('news_event_id')->constrained()->nullOnDelete();
        });
        // Full text lives apart from articles so event/timeline queries never drag bodies along.
        // Stored for internal analysis only; the API serves titles and links, never the body.
        Schema::create('article_contents', function (Blueprint $table) {
            $table->foreignId('article_id')->primary()->constrained()->cascadeOnDelete();
            $table->string('status', 20)->comment('ok | empty | failed');
            $table->longText('body')->nullable(); $table->unsignedInteger('char_count')->default(0);
            $table->char('body_hash', 64)->nullable()->index(); $table->string('extractor', 100)->nullable();
            $table->unsignedSmallInteger('http_status')->nullable(); $table->string('error', 500)->nullable();
            $table->dateTime('fetched_at'); $table->timestamps();
        });

        $now = now();
        $sources = [
            ['udn', '聯合新聞網', 'https://udn.com', 'https://udn.com/news/rssfeed/6638', '報紙', '聯合報系', '^https://udn\.com/news/story/(6656|6657|10930)/\d+', null],
            ['cna', '中央社', 'https://www.cna.com.tw', 'https://feeds.feedburner.com/rsscna/politics', '通訊社', '中央通訊社', '^https://www\.cna\.com\.tw/news/\w+/\d+\.aspx', null],
            ['ltn', '自由時報', 'https://news.ltn.com.tw', 'https://news.ltn.com.tw/rss/politics.xml', '報紙', '自由時報', '^https://news\.ltn\.com\.tw/news/\w+/\w+/\d+', null],
            ['pts', '公視新聞網', 'https://news.pts.org.tw', 'https://news.pts.org.tw/xml/newsfeed.xml', '公共媒體', '公共電視', '^https://news\.pts\.org\.tw/article/\d+', null],
            ['ettoday', 'ETtoday新聞雲', 'https://www.ettoday.net', 'https://feeds.feedburner.com/ettoday/news', '網路媒體', '東森', '^https://www\.ettoday\.net/news/\d+/\d+\.htm', null],
            ['newtalk', '新頭殼', 'https://newtalk.tw', 'https://newtalk.tw/rss/all', '網路媒體', null, '^https://newtalk\.tw/news/view/[\d-]+/\d+', null],
            ['storm', '風傳媒', 'https://www.storm.mg', 'https://www.storm.mg/api/getRss/channel_id/2', '網路媒體', null, '^https://www\.storm\.mg/article/\d+', ['^/(\d+)', 'https://www.storm.mg/article/\1']],
            ['twreporter', '報導者', 'https://www.twreporter.org', 'https://www.twreporter.org/a/rss2.xml', '非營利深度媒體', null, '^https://www\.twreporter\.org/a/[\w-]+', null],
            ['yahoo', 'Yahoo奇摩新聞', 'https://tw.news.yahoo.com', 'https://tw.news.yahoo.com/rss/politics', '入口網站（轉載）', null, '^https://tw\.news\.yahoo\.com/', null],
            ['bbc-zh', 'BBC中文', 'https://www.bbc.com/zhongwen/trad', 'https://feeds.bbci.co.uk/zhongwen/trad/rss.xml', '外媒中文', 'BBC', '^https://www\.bbc\.com/zhongwen/articles/\w+', null],
            ['dw-zh', '德國之聲中文', 'https://www.dw.com/zh', 'https://rss.dw.com/rdf/rss-chi-all', '外媒中文', 'Deutsche Welle', '^https://www\.dw\.com/zh/', null],
            // Fact-check reports are reference material, not coverage; kept off until claim matching exists.
            ['tfc', '台灣事實查核中心', 'https://tfc-taiwan.org.tw', 'https://tfc-taiwan.org.tw/feed/', '事實查核', null, '^https://tfc-taiwan\.org\.tw/', null],
        ];
        DB::table('sources')->insert(array_map(fn ($s) => [
            'slug' => $s[0], 'name' => $s[1], 'homepage_url' => $s[2], 'feed_url' => $s[3], 'media_type' => $s[4], 'owner' => $s[5],
            'link_pattern' => $s[6], 'link_rewrite' => $s[7] ? json_encode($s[7]) : null, 'is_active' => $s[0] !== 'tfc',
            // The density heuristic picks BBC's cookie notice and nearly ties UDN's body with its related-story list.
            'content_selector' => ['udn' => 'section.article-content__editor', 'bbc-zh' => 'main'][$s[0]] ?? null,
            'created_at' => $now, 'updated_at' => $now,
        ], $sources));
        // Articles imported before this table existed only carry the display name.
        foreach (DB::table('sources')->pluck('id', 'name') as $name => $id) {
            DB::table('articles')->where('source', $name)->whereNull('source_id')->update(['source_id' => $id]);
        }
    }
    public function down(): void {
        Schema::dropIfExists('article_contents');
        Schema::table('articles', function (Blueprint $table) { $table->dropConstrainedForeignId('source_id'); });
        Schema::dropIfExists('sources');
    }
};
