from sqlalchemy import inspect, text


def add_missing_columns(engine, metadata):
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    preparer = engine.dialect.identifier_preparer

    with engine.begin() as connection:
        for table in metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            existing_columns = {column['name'] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns or not column.nullable:
                    continue
                column_type = column.type.compile(dialect=engine.dialect)
                connection.execute(text(
                    f'ALTER TABLE {preparer.quote(table.name)} ADD COLUMN {preparer.quote(column.name)} {column_type}'
                ))
