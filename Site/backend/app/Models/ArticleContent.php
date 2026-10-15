<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class ArticleContent extends Model
{
    protected $primaryKey = 'article_id';
    public $incrementing = false;
    protected $guarded = [];
    // Full text is for internal analysis only; never serialise it into API responses.
    protected $hidden = ['body'];
    protected function casts(): array { return ['fetched_at' => 'immutable_datetime']; }
    public function article(): BelongsTo { return $this->belongsTo(Article::class); }
}
