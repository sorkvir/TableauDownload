import configparser
import sqlite3
import os
import sys
import argparse
import psycopg2
 
config = configparser.ConfigParser()
config.read('params.cfg')
 
#pg tables selection
pg_tblsNames = ['workbooks', 'views']
 
#sqlite args
dbsqlite_location = config.get('Sqlite',os.path.normpath('dbsqlite_location'))
dbsqlite_fileName = config.get('Sqlite','dbsqlite_fileName')
dbsqlite_sql = config.get('Sqlite','dbsqlite_sql')
 
parser = argparse.ArgumentParser(description='Tableau data extraction solution by bicortex.com')
 
#tableau server args
parser.add_argument('-n','--hostname', help='Tableau postgresql server name', required=True)
parser.add_argument('-d','--dbname', help='Tableau postgresql database name', required=True)
parser.add_argument('-u','--username', help='Tableau postgresql user name', required=True)
parser.add_argument('-p','--passwd', help='Tableau postgresql password', required=True)
args = parser.parse_args()
 
if not args.hostname or not args.dbname or not args.username or not args.passwd:
    parser.print_help()
 
def run_DB_built(dbsqlite_sql, dbsqlite_location, dbsqlite_fileName, dbname, username, hostname, passwd, *args):
    with sqlite3.connect(os.path.join(dbsqlite_location, dbsqlite_fileName)) as sqlLiteConn:
        sqlLiteConn.text_factory = lambda x: x.unicode('utf-8', 'ignore')              
 
        operations=[]
        commands=[]
        sql={}
 
        #get all SQL operation types as defined by the '----SQL' prefix in tableau_export.sql file
        print('Reading tableau_export.sql file...')
        with open(dbsqlite_sql, 'r') as f:        
            for i in f:
                if i.startswith('----'):
                    i=i.replace('----','')
                    operations.append(i.rstrip('\n'))
        f.close()                
 
        #get all SQL DML &amp; DDL statements from tableau_export.sql file
        tempCommands=[]
        f = open(dbsqlite_sql, 'r').readlines()
        for i in f:
            tempCommands.append(i)
        l = [i for i, s in enumerate(tempCommands) if '----' in s]
        l.append((len(tempCommands)))    
        for first, second in zip(l, l[1:]):
            commands.append(''.join(tempCommands[first:second]))       
        sql=dict(zip(operations, commands))
 
        #run database CREATE SQL
        print('Building TableauEX.db database schema... ')
        sqlCommands = sql.get('SQL 1: Create DB').split(';')
        for c in sqlCommands:
            try:
                sqlLiteConn.execute(c)
            except sqlite3.OperationalError as e:
                print (e)
                sqlLiteConn.rollback()
                sys.exit(1)
            else:
                sqlLiteConn.commit()
 
        #acquire PostgreSQL workgroup database data and populate SQLite database schema with that data  
        print('Acquiring Tableau PostgreSQL data and populating SQLite database for the following tables: {0}...'.format(', '.join(map(str, pg_tblsNames)))) 
        pgConn = "dbname={0} user={1} host={2} password={3} port=8060".format(dbname, username, hostname, passwd)       
        pgConn = psycopg2.connect(pgConn)         
        pgCursor = pgConn.cursor()
        for tbl in pg_tblsNames:
            try:
                tbl_cols={}
                pgCursor.execute("""SELECT ordinal_position, column_name 
                                FROM information_schema.columns 
                                WHERE table_name = '{}' 
                                AND table_schema = 'public'
                                AND column_name != 'index'
                                ORDER BY 1 ASC""".format(tbl)) 
                rows = pgCursor.fetchall()
                for row in rows:                
                    tbl_cols.update({row[0]:row[1]})
                sortd = [tbl_cols[key] for key in sorted(tbl_cols.keys())]
                cols = ",".join(sortd)   
                pgCursor.execute("SELECT {} FROM {}".format(cols,tbl)) 
                rows = pgCursor.fetchall()
                num_columns = max(len(rows[0]) for t in rows)            
                pgsql="INSERT INTO {} ({}) VALUES({})".format(tbl[:-1],cols,",".join('?' * num_columns))
                sqlLiteConn.executemany(pgsql,rows)
             
            except psycopg2.Error as e:
                print(e)
                sys.exit(1)  
            else:               
                sqlLiteConn.commit()
 
        #update SQLite bridging tables based on DML statements under 'SQL 2: Update DB' opertation type header                  
        print('Updating SQLite database bridging tables...')
        sqlCommands = sql.get('SQL 2: Update DB').split(';')
        for c in sqlCommands:
            try:
                sqlLiteConn.execute(c)
            except sqlite3.OperationalError as e:
                print (e)
                sqlLiteConn.rollback()
                sys.exit(1)
            else:
                sqlLiteConn.commit()
     
    sqlLiteConn.close()
    pgConn.close()    
 
if __name__ == "__main__":  
    run_DB_built(dbsqlite_sql, dbsqlite_location, dbsqlite_fileName, args.dbname, args.username, args.hostname, args.passwd, pg_tblsNames) 
