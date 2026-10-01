CREATE CONSTRAINT user_name_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.name IS UNIQUE;

CREATE CONSTRAINT mattress_type_name_unique IF NOT EXISTS
FOR (m:MattressType) REQUIRE m.name IS UNIQUE;
