import pymysql.cursors
"""
    PREREQUISITE:

    CREATE TABLE deal_detail(
        id                  INT(11) UNSIGNED AUTO_INCREMENT, 
        name                TEXT, 
        time                TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP, 
        exp_date            TEXT, 
        orig_price          TEXT, 
        sale_price          TEXT, 
        description         TEXT, 
        short_description  TEXT, 
        fine_print          TEXT, 
        address             TEXT, 
        city                TEXT, 
        href                TEXT, 
        yelp_info           TEXT, 
        opt_count           INT(30), 
        opt_number          TEXT,
        parent_ID           TEXT,
        PRIMARY KEY (id)
    );

    CREATE TABLE deals(
        id              INT(11) UNSIGNED AUTO_INCREMENT,
        href            TEXT,
        item_id         TEXT,
        opt_number      TEXT,
        bought_count    TEXT,
        temp_price      TEXT,
        groupon_rating  TEXT,
        facebook_count  TEXT,
        twitter_count   TEXT,
        sold_out        INT(2),
        expired         INT(2),
        alive           INT(2),
        time            DATETIME DEFAULT CURRENT_TIMESTAMP,
        primary key (id)
    );

    drop table deals;
    drop table deal_detail;

    truncate table deals;
    truncate table deal_detail;

    

    """

class sql_miner:
    deal_data = {}
    connection = None

    def __init__(self, datamine):
        global deal_data
        global connection
        deal_data = datamine
        connection = self.connect()

    def connect(self):
        # Connect to the database
        connection = pymysql.connect(host='localhost',
                             user='root',
                             password='',
                             db='', #
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)
        return connection

    def insert_single(self):
        try:
            with connection.cursor() as cursor:
                sql = "INSERT INTO `deal_detail` (`name`, `exp_date`, `orig_price`, `sale_price`, `description`, `short_description`, `fine_print`, `address`, `city`, `href`, `yelp_info`, `opt_count`, `opt_number`, `parent_ID`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, 
                    (deal_data['name'], deal_data['exp_date'], deal_data['orig_price'], deal_data['sale_price'], 
                        deal_data['description'], deal_data['short_description'], deal_data['fine_print'], 
                        deal_data['address'], deal_data['city'], deal_data['href'], deal_data['yelp_info'], 
                        deal_data['opt_count'], deal_data['opt_number'], deal_data['parent_ID']))
            connection.commit()
        except Exception as e:
            print(e)
            pass
        finally:
            connection.close()

    def insert_single_price(self):
        try:
            with connection.cursor() as cursor:
                sql = "SELECT id FROM `deal_detail` WHERE `href` = %s AND `parent_ID` = %s"
                cursor.execute(sql, (deal_data['href'], 0))
                item_id = cursor.fetchall()[0]['id']
                sql = "INSERT INTO `deals` (`href`, `item_id`, `opt_number`, `bought_count`, `temp_price`, `groupon_rating`, `facebook_count`, `twitter_count`, `sold_out`, `expired`, `alive`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (deal_data['href'], item_id, deal_data['opt_number'], deal_data['bought_count'], deal_data['temp_price'], deal_data['groupon_rating'], 
                    deal_data['facebook_count'], deal_data['twitter_count'], deal_data['sold_out'], deal_data['expired'], deal_data['alive']))
            connection.commit()
        except Exception as e:
            print(e)
            pass
        finally:
            connection.close()

    def insert_option(self):
        # Precondition: Parent Deal has been inserted already.
        try:
            with connection.cursor() as cursor:
                sql = "SELECT id FROM `deal_detail` WHERE `href` = %s" #load parent ID
                cursor.execute(sql, (deal_data['href']))
                parent_ID = cursor.fetchall()[0]['id']

                sql = "INSERT INTO `deal_detail` (`name`, `exp_date`, `orig_price`, `sale_price`, `description`, `short_description`, `fine_print`, `address`, `city`, `href`, `yelp_info`, `opt_count`, `opt_number`, `parent_ID`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, 
                    (deal_data['name'], deal_data['exp_date'], deal_data['orig_price'], deal_data['sale_price'], 
                        deal_data['description'], deal_data['short_description'], deal_data['fine_print'], 
                        deal_data['address'], deal_data['city'], deal_data['href'], deal_data['yelp_info'], 
                        deal_data['opt_count'], deal_data['opt_number'], parent_ID))
            connection.commit()
        except Exception as e:
            print(e)
            pass
        finally:
            connection.close()

    def insert_option_price(self):
        try:
            with connection.cursor() as cursor:
                sql = "SELECT id FROM `deal_detail` WHERE `href` = %s AND `opt_number` = %s"
                cursor.execute(sql, (deal_data['href'], deal_data['opt_number']))
                item_id = cursor.fetchall()[0]['id']

                sql = "INSERT INTO `deals` (`href`, `item_id`, `opt_number`, `bought_count`, `temp_price`, `groupon_rating`, `facebook_count`, `twitter_count`, `sold_out`, `expired`, `alive`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (deal_data['href'], item_id, deal_data['opt_number'], deal_data['bought_count'], deal_data['temp_price'], deal_data['groupon_rating'], 
                    deal_data['facebook_count'], deal_data['twitter_count'], deal_data['sold_out'], deal_data['expired'], deal_data['alive']))
            connection.commit()
        except Exception as e:
            print(e)
            pass
        finally:
            connection.close()



    def read(self):
        print("reading from database...")

        try:
            with connection.cursor() as cursor:
                # Read a single record
                sql = "SELECT * FROM `deal_detail`" # WHERE `email`=%s"
                cursor.execute(sql)

            result = cursor.fetchall()
            print(result)

            #result = cursor.fetchone()
            #while result != None:
            #    print(result['password'])
            #    result = cursor.fetchone()
        except Exception as e:
        	print(e)
        	pass
        finally:
            connection.close()

    def display(self):
        print(deal_data['name'])
        print(deal_data['exp_date'])
        print(deal_data['orig_price'], deal_data['sale_price'])
        print(deal_data['description'])
        print(deal_data['mobile_description'])
        print(deal_data['fine_print'])
        print(deal_data['address'])
        print(deal_data['city'])
        print(deal_data['href'])
        print(deal_data['yelp_info'])
        print(deal_data['opt_count']) 
        print(deal_data['bought_count'])
        print(deal_data['temp_price'])
        print(deal_data['groupon_rating'], deal_data['facebook_count'], deal_data['twitter_count'], deal_data['sold_out'], deal_data['expired'])
