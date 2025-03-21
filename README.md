# CineplexWork
A Python package to automatically convert a Cineplex employees work schedule to a iCalendar file.

## Getting Started
> [!NOTE]
> Official Docker images are available at [jaidenlabelle/cineplexwork](https://hub.docker.com/r/jaidenlabelle/cineplexwork) on Docker Hub.

## Installation
CineplexWork is not available on PyPI and is currently only tested with `Python >= 3.13`.

Download CineplexWork from the repository:
```
git clone https://github.com/jaidenlabelle/cineplex-timetable-exporter
```

Change directory to the newly created folder and run the package as a command-line tool:
```
cd cineplex-timetable-exporter
python -m cineplexwork -h
```

## Docker Compose
Example Docker compose setup when using the official Docker image.
```yaml
services:
  cineplexwork:
    image: 'jaidenlabelle/cineplex:latest'
    container_name: cineplexwork
    restart: no # Avoid restart loop if something bad happens (recommended)
    environment:
      - CINEPLEX_USERNAME=<username>
      - CINEPLEX_PASSWORD=<password>
      - CINEPLEX_TOTP_SECRET=<totp secret>
      - timezone=America/Toronto
      - filename=output/output.ics
      - time=05:00 # UTC time to run the script daily
    volumes:
      - ./data/output:/app/output # iCal file output directory
```

