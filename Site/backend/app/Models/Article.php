<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Article extends Model
{
    protected $guarded = [];
    protected function casts(): array { return ['published_at' => 'immutable_datetime', 'imported_at' => 'immutable_datetime', 'assessments' => 'array', 'is_demo' => 'boolean']; }
    public function newsEvent(): BelongsTo { return $this->belongsTo(NewsEvent::class); }
}
