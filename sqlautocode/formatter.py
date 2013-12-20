import sqlalchemy
import config, constants, util

def textclause_repr(self):
    return 'text(%r)' % self.text

def table_repr(self):
    data = {
        'name': self.name,
        'columns': constants.NLTAB.join([repr(cl) for cl in self.columns]),
        'constraints': constants.NLTAB.join(
            [repr(cn) for cn in self.constraints if not isinstance(cn, sqlalchemy.CheckConstraint)]),
        'index': '',
        'schema': self.schema != None and "schema='%s'" % self.schema or '',
        'options' : '',
        }

    #Optional keyword arguments to the table
    if hasattr(self, 'kwargs'):
        opts = {}
        if 'mysql_engine' in self.kwargs:
            opts['mysql_engine'] = str(self.kwargs['mysql_engine'])
        if 'mysql_default charset' in self.kwargs:
            opts['mysql_charset'] = str(self.kwargs['mysql_default charset'])
        if 'mysql_collate' in self.kwargs:
            opts['mysql_collate'] = str(self.kwargs['mysql_collate'])
        data['options'] = ", ".join(['%s=\'%s\'' % (k, v) for (k, v) in opts.items()])

    if data['constraints']:
        data['constraints'] = data['constraints'] + ','

    return util.as_out_str(constants.TABLE % data)

def _repr_coltype_as(coltype, as_type):
    """repr a Type instance as a super type."""

    specimen = object.__new__(as_type)
    specimen.__dict__ = coltype.__dict__
    return repr(specimen)

def column_repr(self):
    kwarg = []
    if self.key != self.name:
        kwarg.append( 'key')

    if hasattr(self, 'primary_key'):
        kwarg.append( 'primary_key')

    if not self.nullable:
        kwarg.append( 'nullable')
    if self.onupdate:
        kwarg.append( 'onupdate')
    if self.default:
        kwarg.append( 'server_default')
    elif self.server_default:
        self.default = self.server_default.arg
        kwarg.append( 'server_default')

    kwarg.append('autoincrement')
    if not self.autoincrement:
        self.autoincrement = False

    ks = ', '.join('%s=%r' % (k, getattr(self, k)) for k in kwarg )

    name = self.name

    if any(isinstance(self.type, t) for t in \
           [sqlalchemy.dialects.mysql.base.INTEGER, \
            sqlalchemy.dialects.mysql.base.SMALLINT, \
            sqlalchemy.dialects.mysql.base.MEDIUMINT, \
            sqlalchemy.dialects.mysql.base.TINYINT, \
            sqlalchemy.dialects.mysql.base.BIGINT]):
        coltype = '%s(display_width=%s, unsigned=%s)' \
            % (self.type.__class__.__name__, self.type.display_width, self.type.unsigned)
    elif isinstance(self.type, sqlalchemy.dialects.mysql.base.FLOAT):
        float_args = []
        if self.type.precision:
            float_args.append("precision=%s" % self.type.precision)
        if self.type.scale:
            float_args.append("scale=%s" % self.type.scale)
        if self.type.unsigned:
            float_args.append("unsigned=%s" % self.type.unsigned)
        coltype = 'FLOAT(%s)' % ", ".join(float_args)
    elif isinstance(self.type, sqlalchemy.dialects.mysql.base.ENUM):
        enum_args = ['\'%s\'' % str(e) for e in self.type.enums]
        if self.type.charset:
            enum_args.append('charset=\'%s\'' % self.type.charset)
        if self.type.collation:
            enum_args.append('collation=\'%s\'' % self.type.collation)
        coltype = 'ENUM(%s)' % ', '.join(enum_args)
    elif isinstance(self.type, sqlalchemy.dialects.mysql.base.VARCHAR):
        varchar_args = ['length=' + str(self.type.length)]
        if self.type.collation:
            varchar_args.append('collation=\'%s\'' % self.type.collation)
        if self.type.charset:
            varchar_args.append('charset=\'%s\'' % self.type.charset)
        coltype = 'VARCHAR(%s)' % ", ".join(varchar_args)
    elif any(isinstance(self.type, t) for t in \
           [sqlalchemy.dialects.mysql.base.TEXT, \
            sqlalchemy.dialects.mysql.base.MEDIUMTEXT, \
            sqlalchemy.dialects.mysql.base.LONGTEXT]):
        text_args = []
        if self.type.collation:
            text_args.append('collation=\'%s\'' % self.type.collation)
        if self.type.charset:
            text_args.append('charset=\'%s\'' % self.type.charset)
        coltype = '%s(%s)' % (self.type.__class__.__name__, ", ".join(text_args))
    else:
        coltype = repr(self.type)

    data = {'name': self.name,
            'type': coltype,
            'constraints': ', '.join([repr(cn) for cn in self.constraints]),
            'args': ks and ks or '',
            }

    if data['constraints']:
        if data['constraints']: data['constraints'] = ', ' + data['constraints']
    if data['args']:
        if data['args']: data['args'] = ', ' + data['args']

    return util.as_out_str(constants.COLUMN % data)

def foreignkeyconstraint_repr(self):
    options = {}
    if self.onupdate:
        options['onupdate'] = self.onupdate
    if self.ondelete:
        options['ondelete'] = self.ondelete

    #TODO Don't like this hack of name and spec to strip out table... is there a better way?
    data = {'name': repr(self.name),
            'names': repr([".".join(x.parent.name.split(".")[min(1, len(x.parent.name.split("."))-2):]) for x in self.elements]),
            'specs': repr([".".join(x._get_colspec().split(".")[min(1, len(x._get_colspec().split("."))-2):]) for x in self.elements]),
            'options': ", ".join(['%s=\'%s\'' % (k, v) for (k,v) in options.items()])
            }
    return util.as_out_str(constants.FOREIGN_KEY % data)

def primarykeyconstraint_repr(self):
    data = {'columns' : ", ".join(["'%s'" % c.name for c in  self.columns])}
    return util.as_out_str(constants.PRIMARY_KEY % data)

def index_repr(index):
    cols = []
    for column in index.columns:
        # FIXME: still punting on the issue of unicode table names
        if util.is_python_identifier(column.name):
            cols.append('%s.c.%s' % (column.table.name, column.name))
        else:
            cols.append('%s.c[%r]' % (column.table.name, column.name))

    data = {'name': repr(index.name),
            'columns': ', '.join(cols),
            'unique': repr(index.unique),
            }
    return util.as_out_str(constants.INDEX % data)

def monkey_patch_sa():
    sqlalchemy.sql.expression._TextClause.__repr__ = textclause_repr
    sqlalchemy.schema.Table.__repr__ = table_repr
    sqlalchemy.schema.Column.__repr__ = column_repr
    sqlalchemy.schema.ForeignKeyConstraint.__repr__ = foreignkeyconstraint_repr
    sqlalchemy.schema.PrimaryKeyConstraint.__repr__ = primarykeyconstraint_repr
    sqlalchemy.schema.Index.__repr__ = index_repr
