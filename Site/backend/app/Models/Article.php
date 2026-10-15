<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasOne;

class Article extends Model
{
    protected $guarded = [];
    protected function casts(): array { return ['published_at' => 'immutable_datetime', 'imported_at' => 'immutable_datetime', 'assessments' => 'array', 'is_demo' => 'boolean']; }
    public function newsEvent(): BelongsTo { return $this->belongsTo(NewsEvent::class); }
    // Not named source(): the `source` column holds the display name the UI already reads.
    public function mediaSource(): BelongsTo { return $this->belongsTo(Source::class, 'source_id'); }
    public function content(): HasOne { return $this->hasOne(ArticleContent::class); }
}
