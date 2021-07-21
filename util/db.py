"""Shared database code"""

import math
import dateutil
import time
import dateutil.parser
import datetime
import os
import psycopg2
import psycopg2.extras 
import io
import subprocess
import shlex
import pandas as pd
import logging
import re
import numpy as np
import sys

# query parameter value required for driver
PARAM = "%s"

#DB_HOST = '172.18.0.200'
DB_HOST = 'db'
DB_PORT = 5432
DB_NAME = 'FireGUARD'
DB_USER = 'wx_readwrite'
DB_PASSWORD = 'wx_r34dwr1t3p455w0rd!'
#DB_USER = 'docker'
#DB_PASSWORD = 'docker'

def make_insert_statement(table, columns, no_join=True):
    """!
    Generates INSERT statement for table using column names
    @param table Table to insert into
    @param columns Columns within table
    @param no_join Whether or not to make complex statement with join
    @return INSERT statement that was created
    """
    if no_join:
        return "INSERT INTO {table}({cols}) values {vals}".format(
                table=table,
                cols=', '.join(columns),
                vals=PARAM
            )
    return """
INSERT INTO {table}({cols})
SELECT {val_cols}
FROM (VALUES {vals}) val ({cols})
LEFT JOIN {table} d ON
    {join_stmt}
WHERE
    {null_stmt}
    """.format(
        table=table,
        cols=', '.join(columns),
        val_cols=', '.join(map(lambda x: 'val.' + x, columns)),
        join_stmt=' AND '.join(map(lambda x: 'val.' + x + '=d.' + x, columns)),
        null_stmt=' AND '.join(map(lambda x: 'd.' + x + ' IS NULL', columns)),
        vals=PARAM
    )


def make_sub_insert_statement(table, columns, fkId, fkName, fkTable, fkColumns):
    """!
    Generates INSERT statement for table using column names
    @param table Table to insert into
    @param columns Columns within table
    @param fkId Foreign key ID
    @param fkName Foreign key name
    @param fkTable Foreign key table
    @param fkColumns Foreign key table columns
    @return INSERT statement that was created
    """
    # do this instead of using set() so order is kept
    actual_columns = [x for x in columns if x not in fkColumns]
    return """
        INSERT INTO {table}({actual_cols})
        SELECT d.{fkId} AS {fkName}, {val_cols}
        FROM
            (VALUES {vals}) val ({cols})
            LEFT JOIN {fkTable} d
            ON {join_stmt}
        """.format(
                table=table,
                actual_cols=', '.join([fkName] + actual_columns),
                cols=', '.join(columns),
                vals=PARAM,
                fkId=fkId,
                fkName=fkName,
                val_cols=', '.join(map(lambda x: 'val.' + x, actual_columns)),
                fkTable=fkTable,
                join_stmt=' AND '.join(map(lambda x: 'val.' + x + '=d.' + x, fkColumns))
            )


def fix_None(x):
    """!
    Convert to None instead of alternative formats that mean the same
    @param x Value to convert from
    @return None or the original value
    """
    # for some reason comparing to pd.NaT doesn't work
    return None if isinstance(x, type(pd.NaT)) else None if 'nan' == str(x) else x


def fix_Types(x):
    """!
    Convert to datetime if it's a np.datetime64, or None if it's a value for nothing
    @param x Value to convert from
    @return None, a datetime, or the original value
    """
    # for some reason the dates are giving too much precision for the database to use if seconds are specified
    if isinstance(x, np.datetime64):
        x = pd.to_datetime(x, utc=True)
    if isinstance(x, np.int64):
        x = int(x)
    return fix_None(x)


def fix_execute(cursor, stmt, data):
    """!
    @param cursor Cursor to execute statement with
    @param stmt Statement to execute
    @param data Data to populate statement with
    @return None
    """
    try:
        print(stmt)
        if 'DELETE' in stmt:
            psycopg2.extras.execute_batch(cursor, stmt, data, page_size=100000)
        else:
            psycopg2.extras.execute_values(cursor, stmt, (tuple(map(fix_Types, x)) for x in data))
        # doesn't want to work
        # cursor.execute("PREPARE stmt AS {}".format(stmt))
        # execute_batch(cur, "EXECUTE stmt (%s)", params_list)
        # cursor.execute("DEALLOCATE stmt")
    except psycopg2.Error as e:
        logging.error(e)
        sys.exit(-1)

def open_local_db():
    """!
    @param dbname Name of database to open, or None to open default
    @return psycopg2 connection to database
    """
    logging.debug("Opening local database connection")
    return psycopg2.connect(dbname=DB_NAME, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)


def save_data(table, wx, delete_all=False, dbname=None):
    """!
    Save into database
    @param table Table to save data into
    @param wx Data to save into table
    @param delete_all Whether or not to delete data from table before saving
    @param dbname Name of database to save to
    @return None
    """
    # open connection
    cnxn = None
    try:
        cnxn = open_local_db(dbname)
        trans_save_data(cnxn, table, wx, delete_all)
        cnxn.commit()
    finally:
        if cnxn:
            cnxn.close()


def trans_delete_data(cnxn, table, wx, delete_all=False):
    """!
    Delete data give from table so that it can be replaced
    @param cnxn Connection to use for query
    @param table Table to insert data into
    @param wx Data to insert into table
    @param delete_all Whether or not to delete all data from table before inserting
    @return None
    """
    cursor = cnxn.cursor()
    # Assumption is that every save we have all points for the included members
    # - still should allow us to save one member at a time though
    if delete_all:
        stmt_delete = "DELETE FROM {}".format(table)
        logging.debug("Deleting existing data using {}".format(stmt_delete))
        cursor.execute(stmt_delete)
    else:
        # DELETE statement that uses all unique values for index columns except coordinates
        non_point_indices = [x for x in wx.index.names if x not in ['latitude', 'longitude']]
        unique = wx.reset_index()[non_point_indices].drop_duplicates()
        stmt_delete = "DELETE FROM {} WHERE {}".format(table,
                                                       ' and '.join(map(lambda x: x + '=' + PARAM, non_point_indices))
                                                       )
        logging.debug("Deleting existing data using {}".format(stmt_delete))
        logging.debug(unique.values)
        if 0 == len(unique.values):
            logging.debug("No data provided - nothing to delete or insert")
            return
        fix_execute(cursor, stmt_delete.format(table), unique.values)


def trans_save_data(cnxn, table, wx, delete_all=False):
    """!
    Save into database with given connection and don't commit
    @param cnxn Connection to use for query
    @param table Table to insert data into
    @param wx Data to insert into table
    @param delete_all Whether or not to delete all data from table before inserting
    @return None
    """
    logging.debug("Saving data to {}".format(table))
    trans_delete_data(cnxn, table, wx, delete_all)
    all_wx = wx.reset_index()
    columns = all_wx.columns
    stmt_insert = make_insert_statement(table, columns)
    trans_insert_data(cnxn, wx, stmt_insert)

def trans_insert_data(cnxn, wx, stmt_insert):
    """!
    Insert data using statement
    @param cnxn Connection to use for query
    @param wx Data to insert into table
    @param stmt_insert INSERT statement to use
    @return None
    """
    cursor = cnxn.cursor()
    index = wx.index.names
    all_wx = wx.reset_index()
    # HACK: this is returning int64 when we know they aren't
    for i in index:
        # logging.debug("Fixing column " + str(i))
        if 'int64' in str(all_wx[i].dtype):
            all_wx[i] = all_wx[i].astype(int)
    logging.debug("Inserting {} rows into database".format(len(all_wx)))
    # use generator expression instead of list so we don't convert and then use
    fix_execute(cursor, stmt_insert, all_wx.values)


def write_foreign(cnxn, schema, table, index, fct_insert, cur_df):
    """!
    Write data subset for a foreign key table and then merge the generated foreign keys into data
    @param cnxn Connection to use for query
    @param schema Schema that table resides in
    @param table Table to insert into
    @param index List of index keys for table
    @param fct_insert Function to call to insert into table
    @param cur_df DataFrame with data to insert
    @return DataFrame with original data and merged foreign key data
    """
    qualified_table = '{}.{}'.format(schema, table)
    logging.debug('Writing foreign key data to {}'.format(qualified_table))
    new_index = cur_df.index.names
    cur_df = cur_df.reset_index()
    sub_data = cur_df[index].drop_duplicates().set_index(index)
    fct_insert(cnxn, qualified_table, sub_data)
    # should be much quicker to read out the fk data and do a join on this end
    fkData = pd.read_sql("SELECT * FROM {}".format(qualified_table), cnxn)
    # logging.debug(fkData.columns)
    # logging.debug(fkData.dtypes)
    for i in range(len(fkData.columns)):
        if fkData.dtypes[i] == 'datetime64[ns]':
            c = fkData.columns[i]
            # logging.debug('Fixing ' + c)
            fkData[c] = pd.to_datetime(fkData[c], utc=True)
    # logging.debug(fkData.dtypes)
    fkId = [x for x in fkData.columns if x not in index][0]
    fkColumns = [x for x in fkData.columns if x != fkId]
    new_index = [fkId] + [x for x in new_index if x not in fkColumns]
    columns = [fkId] + [x for x in cur_df.columns if x not in fkColumns]
    cur_df = cur_df.merge(fkData)[columns].set_index(new_index)
    return cur_df

SCHEMA = None
MODELFK = None
FINAL_TABLE = None
DF = None
def insert_weather(schema, final_table, df, modelFK='generated'):
    """!
    Insert weather data into table and foreign key tables
    @param schema Schema that table exists in
    @param final_table Table to insert into
    @param df DataFrame with data to insert
    @param modelFK Foreign key to use for inserting into DAT_Model table
    @return None
    """
    global SCHEMA
    global MODELFK
    global FINAL_TABLE
    global DF
    SCHEMA = schema
    MODELFK = modelFK
    FINAL_TABLE = final_table
    DF = df
    # schema = common.SCHEMA
    # modelFK = common.MODELFK
    # final_table = common.FINAL_TABLE
    def do_insert(cnxn, table, data):
        """Insert and ignore duplicate key failures"""
        stmt_insert = make_insert_statement(table, data.reset_index().columns, False)
        # don't delete and insert without failure
        trans_insert_data(cnxn, data, stmt_insert)
    def do_insert_only(cnxn, table, data):
        """Insert and assume success because no duplicate keys should exist"""
        # rely on deleting from FK table to remove everything from this table, so just insert
        stmt_insert = make_insert_statement(table, data.reset_index().columns)
        trans_insert_data(cnxn, data, stmt_insert)
    try:
        cnxn = open_local_db()
        cur_df = df
        cur_df = write_foreign(cnxn, schema, 'DAT_Location', ['latitude', 'longitude'], do_insert, cur_df)
        cur_df = write_foreign(cnxn, schema, 'DAT_Model', ['model', modelFK], trans_save_data, cur_df)
        cur_df = write_foreign(cnxn, schema, 'DAT_LocationModel', ['modelgeneratedid', 'locationid'], do_insert_only, cur_df)
        logging.debug('Writing data to {}'.format(final_table))
        do_insert_only(cnxn, '{}.{}'.format(schema, final_table), cur_df)
        cnxn.commit()
    finally:
        cnxn.close()
