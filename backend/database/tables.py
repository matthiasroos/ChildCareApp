import sqlalchemy

children_table = sqlalchemy.table('children',
                                  sqlalchemy.column('child_id'),
                                  sqlalchemy.column('name'),
                                  sqlalchemy.column('sur_name'),
                                  sqlalchemy.column('birth_day'),
                                  sqlalchemy.column('created_at')
                                  )
