<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void {
        // A reprint (e.g. UDN or Yahoo running a CNA wire story verbatim) points at the earliest article with the same text,
        // so event counts and comparisons can skip it. Always the group's root, never a chain; NULL = an original.
        Schema::table('articles', function (Blueprint $table) {
            $table->foreignId('duplicate_of_article_id')->nullable()->after('source_id')->constrained('articles')->nullOnDelete();
        });
        Schema::table('article_contents', function (Blueprint $table) {
            $table->unsignedBigInteger('simhash')->nullable()->after('body_hash')->comment('64-bit SimHash of the body (python_service/prism/dedupe.py); NULL = not fingerprinted or too short');
        });
    }
    public function down(): void {
        Schema::table('article_contents', function (Blueprint $table) { $table->dropColumn('simhash'); });
        Schema::table('articles', function (Blueprint $table) { $table->dropConstrainedForeignId('duplicate_of_article_id'); });
    }
};
