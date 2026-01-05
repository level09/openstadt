# Contributing to OpenStadt | Beitragen zu OpenStadt

[English](#english) | [Deutsch](#deutsch)

---

## English

Thank you for your interest in contributing to OpenStadt! This project aims to make infrastructure equity visible in German cities.

### How to Contribute

#### Report Issues
- Found a bug? [Open an issue](https://github.com/level09/openstadt/issues)
- Have a feature idea? We'd love to hear it!

#### Add Your City
The easiest way to contribute is to add support for a new city:

1. Copy `config/cities/_template.yaml` to `config/cities/your-city.yaml`
2. Configure the city center, bounds, and layers
3. Test locally with `uv run flask load-city config/cities/your-city.yaml`
4. Submit a pull request

#### Code Contributions
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure code quality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone the repo
git clone https://github.com/level09/openstadt.git
cd openstadt

# Setup environment
./setup.sh
# Or manually:
uv sync
cp .env-sample .env
uv run flask create-db
uv run flask install

# Run development server
uv run flask run
```

### Code Style
- Python: Follow PEP 8
- JavaScript: Use ES6+ features
- Keep commits focused and atomic
- Write meaningful commit messages

---

## Deutsch

Vielen Dank für Ihr Interesse an OpenStadt! Dieses Projekt macht Infrastruktur-Gerechtigkeit in deutschen Städten sichtbar.

### Wie Sie beitragen können

#### Fehler melden
- Fehler gefunden? [Issue erstellen](https://github.com/level09/openstadt/issues)
- Feature-Idee? Wir freuen uns darauf!

#### Ihre Stadt hinzufügen
Der einfachste Weg beizutragen ist, eine neue Stadt hinzuzufügen:

1. Kopieren Sie `config/cities/_template.yaml` nach `config/cities/ihre-stadt.yaml`
2. Konfigurieren Sie Stadtzentrum, Grenzen und Ebenen
3. Testen Sie lokal mit `uv run flask load-city config/cities/ihre-stadt.yaml`
4. Erstellen Sie einen Pull Request

#### Code-Beiträge
1. Repository forken
2. Feature-Branch erstellen (`git checkout -b feature/tolles-feature`)
3. Änderungen vornehmen
4. Tests durchführen
5. Änderungen committen (`git commit -m 'Tolles Feature hinzugefügt'`)
6. Branch pushen (`git push origin feature/tolles-feature`)
7. Pull Request öffnen

### Entwicklungsumgebung

```bash
# Repository klonen
git clone https://github.com/level09/openstadt.git
cd openstadt

# Umgebung einrichten
./setup.sh
# Oder manuell:
uv sync
cp .env-sample .env
uv run flask create-db
uv run flask install

# Entwicklungsserver starten
uv run flask run
```

### Code-Stil
- Python: PEP 8 folgen
- JavaScript: ES6+ Features nutzen
- Commits fokussiert und atomar halten
- Aussagekräftige Commit-Nachrichten schreiben

---

## Community

- [Code for Germany](https://codefor.de) - Civic Tech Community
- [Open Knowledge Foundation](https://okfn.de) - Offene Daten für alle

## License | Lizenz

MIT License - see [LICENSE](LICENSE)
