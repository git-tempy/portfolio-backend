# Image uploads

New image uploads are WebP derivatives. The frontend creates WebP in its worker (or fallback canvas), with no JPG/PNG fallback when a smaller input happens to win the byte comparison. The API also converts multipart JPG/PNG uploads and verified direct-upload receipts, so calling the API without the frontend cannot skip conversion. PDFs stay unchanged.

The server limits public image width to 2560px, decoded area to 16 megapixels and longest edge to 20000px, preserving aspect ratio. Long case studies retain their readable width. Alpha is retained and EXIF orientation is baked before metadata is removed. Existing well-sized, metadata-free WebP is not encoded a second time. Animated images are rejected rather than silently flattened. Small PNG may produce a larger WebP; this is a format guarantee, not a guarantee that every file shrinks.

Direct image uploads stage under `private/originals/<admin>/<random>.<ext>`. After validation, the API writes a separate `uploads/<admin>/<random>.webp` derivative, and only that key enters the public model/API. Original bytes are not overwritten or deleted. The frontend normally already sends optimized WebP, so this staging object is the received upload, not an archive of the user's full-resolution desktop original. Multipart images are converted in memory; their input originals are not archived.

Storage must remain a PRIVATE bucket. Existing S3 configuration uses signed read URLs with a one-hour expiry; a prefix named `private` is not an access-control rule on a public bucket. Verify bucket policy at deployment. No storage ACL or bucket policy has been modified here. Production buckets and existing image records have not been changed.

The browser necessarily receives displayed image bytes. Inspect/Network, screenshots or another HTTP client can copy those public preview bytes. Right-click/F12 blocking, canvas and hidden URLs cannot prevent this and are deliberately not presented as protection. Private originals + bounded public derivatives protect source resolution; a burned-in watermark is the additional option for deterring reuse. Signed previews can be copied while valid, and expiry cannot revoke an already downloaded file.

Existing JPG/PNG are now converted lazily by the protected endpoint on first access. Originals and database keys remain intact; derivatives are cached under `previews/v1/`. Keys are treated as immutable (the upload pipeline uses UUIDs). Staged original retention/lifecycle should be configured separately to avoid accumulating abandoned uploads. Do not run a bulk rewrite or delete originals automatically.

## Protected browser delivery

Image fields, and JPG/PNG/WebP stored in generic file fields, serialize to same-origin `/api/media/image/<signed-token>/preview.webp` paths. No S3 URL is generated for these fields. PDFs remain downloadable. Frontend Vercel rewrites this route to the backend; Vite proxies it locally. Deploy the frontend media rewrite first, then the backend in a coordinated release. The old frontend has no media rewrite and cannot render the new relative URLs.

Normal image requests require `Sec-Fetch-Site: same-origin` and `Sec-Fetch-Dest: image`. Document/new-tab navigation, hotlinking and missing metadata are denied. Older browsers or image crawlers that omit Fetch Metadata are intentionally denied as well. `fetch()` for the admin image editor additionally requires a valid staff Bearer token. Public image responses vary on both metadata headers and Authorization, have `private, max-age=300`, CORP same-origin and nosniff; denials use no-store. Vary prevents a cached image response being reused for a document navigation.

This is a browser usage restriction, NOT DRM. An HTTP client can forge metadata headers; users can save already received bytes or screenshots. Signed tokens protect key integrity, not image confidentiality. Original bucket object reads must remain private. A no-signature HEAD request against the supplied example storage object returned 403 during implementation; previously issued signed storage URLs are not revoked by this code and remain usable until they expire. Existing deployed pages/API results/browser caches must refresh after release.

Validation: `manage.py test core.test_uploads core.test_image_processing core.test_protected_media --settings=core.test_settings`; frontend `node --test tests/webp-upload.test.mjs` and `npm run build`.
