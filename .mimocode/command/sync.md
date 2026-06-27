---
description: Pull latest changes from origin and verify working tree is clean
---

# Sync

Pull the latest changes from origin and check status.

## Usage

```
/sync
```

## Steps

1. **Pull latest changes**
   ```bash
   cd /home/sofie/orgchefgroep/cursor-dreaming-sdk && git pull origin main
   ```

2. **Check status**
   ```bash
   git status --short
   ```

3. **Report**
   - Show if there were any conflicts
   - Show any uncommitted changes
   - Suggest next action if needed

## Notes

- Always pulls to main branch
- Safe to run multiple times (idempotent)
- Use before starting new work to stay in sync
