<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    // Yahoo's RSS writes UTC clock times labelled +0800 (e.g. "08:37:24 +0800" for a story LTN dates 16:37:24 +0800),
    // so its articles were stored 8 hours early — early enough to look like the original of the LTN stories it reprints.
    private const YAHOO_OFFSET = 480;

    public function up(): void {
        Schema::table('sources', function (Blueprint $table) {
            $table->smallInteger('pubdate_offset_minutes')->default(0)->after('link_rewrite')->comment('Added to the feed pubDate, for feeds that mislabel their time zone');
        });
        $this->shiftYahoo(self::YAHOO_OFFSET);
    }
    public function down(): void {
        $this->shiftYahoo(-self::YAHOO_OFFSET);
        Schema::table('sources', function (Blueprint $table) { $table->dropColumn('pubdate_offset_minutes'); });
    }
    private function shiftYahoo(int $minutes): void {
        $id = DB::table('sources')->where('slug', 'yahoo')->value('id');
        if ($id === null) { return; }
        DB::table('sources')->where('id', $id)->update(['pubdate_offset_minutes' => $minutes > 0 ? $minutes : 0]);
        DB::table('articles')->where('source_id', $id)->where('is_demo', false)->lazyById()->each(function ($article) use ($minutes) {
            DB::table('articles')->where('id', $article->id)->update(['published_at' => Carbon::parse($article->published_at)->addMinutes($minutes)]);
        });
    }
};
