# Cache tags / render arrays / invalidation

Detail for checklist item 8. These are the higher-value "senior" findings: cache-metadata
bugs render stale content and are hard to spot in review.

## Prefer whole-object cacheable dependencies

- Use `$build['#cache']` via `CacheableMetadata::createFromRenderArray()` +
  `addCacheableDependency($entity)` (or `$renderer->addCacheableDependency($build, $entity)`)
  instead of hand-listing a single cache tag. The object carries its tags, contexts, and
  max-age together, so metadata stays complete as the entity's own dependencies change.

> Instead of adding the single cache tag, add the whole object dependency, which may also carry contexts or a custom max-age: `->addCacheableDependency($node)`.

## Do not duplicate or hand-roll tags

- Do not list the same cache tag twice. For an entity, `user:{$user->id()}` (or the
  entity's own cache tags) is enough.

> We are duplicating the same cache tag here, just use `user:{$user->id()}`.

## Cache contexts

- Check whether a render depends on the current user, and add the `user` cache context
  when it does. Conversely, do not add a context that is already implied or unnecessary.

> Do we need the user cache context here, or is it already present, or not needed at all?

## Cache API, not session

- State that must be invalidated on a change (for example a user's newsletter
  subscription) belongs in the Cache API with proper tags, not in the session. Invalidate
  it when the source changes.

> The subscription info must be handled through the cache API with invalidation, not through the session.

## Responses

- A controller that returns an external redirect should return a
  `TrustedRedirectResponse` and attach the entity as a cache dependency on the response.

## Edge cases to check

- Verify behavior when the cache is disabled (some rendering bugs only appear cache-off).
- When a review bot flags a cache issue, confirm whether it is a real invalidation gap or
  a false positive before dismissing it.
