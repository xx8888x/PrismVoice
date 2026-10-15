<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

return new class extends Migration {
    // Yahoo pages end with a sidebar of story cards whose paragraph text can outweigh a short article, so the density
    // heuristic sometimes stored a related story instead of the body. The body paragraphs sit directly in .atoms; the
    // trailing "更多…報導" link line is left out because it alone pushed real reprints below the reprint threshold.
    private const SELECTOR = 'section.module-article-body .atoms > p:not(.read-more-vendor)';

    public function up(): void {
        DB::table('sources')->where('slug', 'yahoo')->update(['content_selector' => self::SELECTOR]);
    }
    public function down(): void {
        DB::table('sources')->where('slug', 'yahoo')->update(['content_selector' => null]);
    }
};
