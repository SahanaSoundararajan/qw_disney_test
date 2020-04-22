import psycopg2


# Connected to Jupiter Disney OFE DB.
con = psycopg2.connect(
    host = "qw-disney-ofe-jupiter-staging.cuoifh04ilik.us-east-1.rds.amazonaws.com",
    database = "qw_disney_ofe_adapter",
    user = "dbroot",
    password = "EJnPAt2XxArds7MJ")
