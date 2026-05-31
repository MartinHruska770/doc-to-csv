import io
import os
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from converters import (
    SUPPORTED_EXTENSIONS,
    UnsupportedFormat,
    extract_lines,
    sentences_to_csv,
    split_sentences,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/prevod")
def convert():
    upload = request.files.get("soubor")
    if upload is None or not upload.filename:
        flash("Nevybral jsi žádný soubor.")
        return redirect(url_for("index"))

    try:
        lines = extract_lines(upload.stream, Path(upload.filename).suffix)
        csv_text = sentences_to_csv(split_sentences(lines))
    except UnsupportedFormat:
        flash("Podporované formáty: " + ", ".join(sorted(SUPPORTED_EXTENSIONS)))
        return redirect(url_for("index"))
    except Exception:
        app.logger.exception("převod selhal: %s", upload.filename)
        flash("Soubor se nepodařilo zpracovat. Není poškozený?")
        return redirect(url_for("index"))

    if not csv_text:
        flash("V dokumentu se nenašel žádný text k převodu.")
        return redirect(url_for("index"))

    stem = Path(secure_filename(upload.filename)).stem or "dokument"
    return send_file(
        io.BytesIO(csv_text.encode("utf-8")),
        mimetype="text/csv; charset=utf-8",
        as_attachment=True,
        download_name=f"{stem}.csv",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
