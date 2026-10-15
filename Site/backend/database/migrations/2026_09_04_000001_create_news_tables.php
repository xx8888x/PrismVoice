<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void {
        Schema::create('news_events', function (Blueprint $table) {
            $table->id(); $table->string('cluster_key')->unique(); $table->string('title');
            $table->text('description'); $table->json('dimensions');
            $table->boolean('is_demo')->default(false); $table->timestamps();
        });
        Schema::create('articles', function (Blueprint $table) {
            $table->id(); $table->foreignId('news_event_id')->constrained()->cascadeOnDelete();
            $table->string('url', 1000)->nullable(); $table->string('url_hash', 64)->unique();
            $table->string('title', 1000); $table->string('source'); $table->string('author')->nullable();
            $table->string('category')->nullable(); $table->dateTime('published_at')->index();
            $table->dateTime('imported_at'); $table->json('assessments');
            $table->string('analysis_status')->default('unreviewed'); $table->unsignedInteger('revision')->default(1);
            $table->boolean('is_demo')->default(false); $table->timestamps();
        });
    }
    public function down(): void { Schema::dropIfExists('articles'); Schema::dropIfExists('news_events'); }
};
