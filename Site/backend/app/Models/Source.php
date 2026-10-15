<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Source extends Model
{
    protected $guarded = [];
    protected function casts(): array { return ['link_rewrite' => 'array', 'is_active' => 'boolean', 'last_fetched_at' => 'immutable_datetime', 'last_success_at' => 'immutable_datetime']; }
    public function articles(): HasMany { return $this->hasMany(Article::class); }
}
