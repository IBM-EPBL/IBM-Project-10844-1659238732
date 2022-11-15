CREATE TABLE "users" (
  "id" int NOT NULL GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1),
  "first_name" varchar(100) DEFAULT NULL,
  "last_name" varchar(100) DEFAULT NULL,
  "email" varchar(100) DEFAULT NULL,
  "username" varchar(100) DEFAULT NULL,
  "password" varchar(100) DEFAULT NULL,
  "role" varchar(100) DEFAULT 'user',
  "monthly_limit" int NOT NULL DEFAULT '2000',
  PRIMARY KEY("id")
);

CREATE TABLE "transactions"(
  "id" int NOT NULL GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1),
  "user_id" int DEFAULT NULL,
  "amount" int NOT NULL DEFAULT '0',
  "description" varchar(255) DEFAULT NULL,
  "category" varchar (255) DEFAULT NULL,
  "date" timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY("id"),
  KEY "user_id"("user_id"),
  CONSTRAINT "transactions_ibfk_1" FOREIGN KEY("user_id") REFERENCES "users"("id") ON UPDATE NO ACTION ON DELETE CASCADE
);