# Brand configuration

All public product strings and stable project identity values live in `packages/brand/brand.json`. The React package imports the typed brand module, while FastAPI reads the same JSON file mounted into its container.

The configured identity is CiteNook / CiteNook AI, with repository and app ID `cite-nook-ai`, package scope `@citenook/*`, Docker project `citenook`, and story prefix `MRA`.
