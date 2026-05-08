# Changelog

- [2.0.1](#201---05-08-2026)
- [2.0.0](#200---05-07-2026)
- [1.0.0](#100---04-24-2025)

---

## [2.0.1] - 05-08-2026
- Changed output format of the song from `.ogg` to `.wav` since fluidsynth only natively supports `.wav`
- Increased fluidsynth 'gain argument from `0.2` to `1.0` to increase song volume
- Moved `ace.log` from the package to same caching location of the downloaded soundfont
- Added `CONTRIBUTING.MD` and `SECURITY.md`
- Added coding standards on commit
- Updated `README.md`


## [2.0.0] - 05-07-2026
- Removed AWS S3 dependency. Files are now saved locally to the user-specified output directory.
- Removed `.env` configuration requirement - no AWS credentials needed
- Soundfont now downloaded on first run and cached
- `boto3`, `botocore`, `s3transfer`, `python-dotenv` dependencies


## [1.0.0] - 04-24-2025
- Drum track extraction from MIDI files
- Generates a drum-only MIDI file with `_DRUMS` suffix
- Converts drum MIDI to Clone Hero compatible `.chart` file
- Synthesizes audio from MIDI using FluidSynth and uploads to AWS S3
- AWS S3 integration for file storage via `boto3`
- `.env` configuration for AWS credentials
