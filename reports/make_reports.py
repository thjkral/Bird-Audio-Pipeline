from pathlib import Path
import logging

from sqlalchemy import text


def _get_sql_scripts():
    """Return report SQL filenames paired with their absolute paths."""
    scripts_directory = Path(__file__).resolve().parent / "reports_sql"
    return [
        (script.name, str(script.resolve()))
        for script in sorted(scripts_directory.iterdir())
        if script.is_file()
    ]


def _split_sql_statements(sql):
    """Split a SQL script into statements while preserving quoted semicolons."""
    statements = []
    statement = []
    quote = None
    index = 0

    while index < len(sql):
        character = sql[index]

        if quote:
            statement.append(character)
            if character == quote:
                if quote in ("'", '"') and index + 1 < len(sql) and sql[index + 1] == quote:
                    statement.append(sql[index + 1])
                    index += 1
                elif index == 0 or sql[index - 1] != "\\":
                    quote = None
        elif character in ("'", '"', "`"):
            quote = character
            statement.append(character)
        elif character == ";":
            sql_statement = "".join(statement).strip()
            if sql_statement:
                statements.append(sql_statement)
            statement = []
        else:
            statement.append(character)

        index += 1

    sql_statement = "".join(statement).strip()
    if sql_statement:
        statements.append(sql_statement)

    return statements


def generate_reports(db_engine):
    report_files = _get_sql_scripts()
    number_or_reports = len(report_files)
    if number_or_reports == 0:
        logging.warning('No SQL scripts found')
        return

    logging.info(f'Generating {number_or_reports} reports')
    for report_name, report_path in report_files:
        try:
            sql = Path(report_path).read_text(encoding="utf-8")
            statements = _split_sql_statements(sql)

            if not statements:
                logging.warning('No SQL statements found in %s', report_name)
                continue

            with db_engine.begin() as connection:
                for statement in statements:
                    connection.execute(text(statement))
        except Exception as e:
            logging.exception(f'Error generating report: {report_name}:\n{e}')

        logging.info('Generated report from %s', report_name)
