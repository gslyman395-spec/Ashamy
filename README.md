# Ashamy

Minimal backend scaffolding for continuous AI learning is now included:

- Historical signal outcome tracking
- Dynamic global source performance + weekly weight recalculation
- Model version history + rollback support
- Monitoring alerts for accuracy and weight shifts
- API-layer methods matching the requested learning endpoints

Run tests:

```bash
cd /home/runner/work/Ashamy/Ashamy
python -m unittest discover -s tests -v
```