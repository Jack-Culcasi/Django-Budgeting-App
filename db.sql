-- Represents user information
-- This table will be handled by Django's built-in User model.

-- Represent each payday
CREATE TABLE `payday` (
  `id` int PRIMARY KEY NOT NULL AUTO_INCREMENT, -- Unique identifier for the payday
  `user_id` int NOT NULL, -- ID of the user to whom the payday belongs
  `payday_date` datetime NOT NULL, -- Date of payday
  `amount` decimal(15, 2) DEFAULT null, -- Total earned money for the month
  `note` varchar(255) DEFAULT null, -- Additional notes
  CONSTRAINT `fk_payday_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
);

-- Represent a monthly expenses event (every payday)
CREATE TABLE `monthly_expenses` (
  `id` int PRIMARY KEY NOT NULL AUTO_INCREMENT,  -- Unique identifier for the monthly expenses
  `payday_id` int NOT NULL, -- ID of the payday
  `start_date` datetime NOT NULL, -- Start expenses's period
  `end_date` datetime NOT NULL, -- End expenses's period
  `utilities` decimal(15, 2) DEFAULT null, -- Utilities expenses for the month
  `groceries` decimal(15, 2) DEFAULT null, -- Groceries expenses for the month
  `misc` decimal(15, 2) DEFAULT null, -- Miscellaneous expenses for the month
  `amount` decimal(15, 2) DEFAULT null, -- Total money spent for the month
  `note` varchar(255) DEFAULT null, -- Additional notes
  CONSTRAINT `fk_monthly_expenses_payday_id` FOREIGN KEY (`payday_id`) REFERENCES `payday` (`id`)
);

-- Represents a broker 
CREATE TABLE `broker` (
  `id` int PRIMARY KEY NOT NULL AUTO_INCREMENT, -- Unique identifier for the broker
  `user_id` int NOT NULL, -- ID of the user
  `name` varchar(64) NOT NULL, -- Name of the broker
  `amount` decimal(15, 2) DEFAULT null, -- Total invested at the given date
  `latest_update` datetime DEFAULT null, -- Date of the latest update
  `note` varchar(255) DEFAULT null, -- Additional notes
  CONSTRAINT `fk_broker_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
);

-- Represents a bank
CREATE TABLE `bank` (
  `id` int PRIMARY KEY NOT NULL AUTO_INCREMENT, -- Unique identifier for the bank
  `user_id` int NOT NULL, -- ID of the user
  `name` varchar(64) NOT NULL, -- Name of the bank
  `amount` decimal(15, 2) DEFAULT null, -- Amount saved at the given date
  `latest_update` datetime DEFAULT null, -- Date of the latest update
  `note` varchar(255) DEFAULT null, -- Additional notes
  CONSTRAINT `fk_bank_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
);

-- Represents a pension provider
CREATE TABLE `pension` (
  `id` int PRIMARY KEY NOT NULL AUTO_INCREMENT, -- Unique identifier for the savings record
  `user_id` int NOT NULL, -- ID of the user
  `name` varchar(64) NOT NULL, -- Name of the pension provider
  `amount` decimal(15, 2) DEFAULT null, -- Total pension at the given date
  `latest_update` datetime DEFAULT null, -- Date of the latest update
  `note` varchar(255) DEFAULT null, -- Additional notes
  CONSTRAINT `fk_pension_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
);

-- Represents net worth over time
CREATE TABLE `net_worth` (
  `id` int PRIMARY KEY NOT NULL AUTO_INCREMENT, -- Unique identifier for the savings record
  `user_id` int NOT NULL, -- ID of the user
  `payday_id` int NOT NULL, -- ID of the payday
  `date` datetime NOT NULL, -- Date of the net worth record
  `total_savings` decimal(15, 2) DEFAULT null, -- Total savings in banks at the given date
  `total_investments` decimal(15, 2) DEFAULT null, -- Total investments at the given date
  `total_pension` decimal(15, 2) DEFAULT null, -- Total pension at the given date
  `net_worth` decimal(15, 2) DEFAULT null, -- Total net worth at the given date
  `note` varchar(255) DEFAULT null, -- Additional notes
  CONSTRAINT `fk_net_worth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `fk_net_worth_payday_id` FOREIGN KEY (`payday_id`) REFERENCES `payday` (`id`)
);

--- Indexes

-- Creating indexes for the user_id column in each table
CREATE INDEX idx_payday_user_id ON `payday` (`user_id`);
CREATE INDEX idx_monthly_expenses_payday_id ON `monthly_expenses` (`payday_id`);
CREATE INDEX idx_broker_user_id ON `broker` (`user_id`);
CREATE INDEX idx_bank_user_id ON `bank` (`user_id`);
CREATE INDEX idx_pension_user_id ON `pension` (`user_id`);
CREATE INDEX idx_net_worth_user_id ON `net_worth` (`user_id`);

-- Creating an index for the payday_id column in the net_worth table
CREATE INDEX idx_net_worth_payday_id ON `net_worth` (`payday_id`);

--- TRIGGERS

-- Trigger to automatically update the amount field when inserting or updating on monthly_expenses table
CREATE TRIGGER update_monthly_expenses_amount
BEFORE INSERT OR UPDATE ON monthly_expenses
FOR EACH ROW
BEGIN
    SET NEW.amount = NEW.utilities + NEW.groceries + NEW.misc;
END;

-- UPDATE latest_update
-- Trigger to automatically set latest_update to current time on broker table
CREATE TRIGGER update_broker_latest_update
BEFORE INSERT OR UPDATE ON broker
FOR EACH ROW
BEGIN
    SET NEW.latest_update = CURRENT_TIMESTAMP;
END;

-- Trigger to automatically set latest_update to current time on bank table
CREATE TRIGGER update_bank_latest_update
BEFORE INSERT OR UPDATE ON bank
FOR EACH ROW
BEGIN
    SET NEW.latest_update = CURRENT_TIMESTAMP;
END;

-- Trigger to automatically set latest_update to current time on pension table
CREATE TRIGGER update_pension_latest_update
BEFORE INSERT OR UPDATE ON pension
FOR EACH ROW
BEGIN
    SET NEW.latest_update = CURRENT_TIMESTAMP;
END;

-- This procedure will be called by triggers whenever an update or insert occurs in any of the relevant tables (savings, broker, pension)
DELIMITER //

CREATE PROCEDURE update_net_worth(IN user_id INT, IN payday_id INT)
BEGIN
    DECLARE total_savings DECIMAL(15, 2);
    DECLARE total_investments DECIMAL(15, 2);
    DECLARE total_pension DECIMAL(15, 2);
    DECLARE net_worth DECIMAL(15, 2);

    -- Sum the "amount" value for each user's bank 
    SET total_savings = (SELECT IFNULL(SUM(amount), 0) FROM bank WHERE user_id = user_id);

    -- Sum the "amount" value for each user's broker 
    SET total_investments = (SELECT IFNULL(SUM(amount), 0) FROM broker WHERE user_id = user_id);

    -- Sum the "amount" value for each user's pension 
    SET total_pension = (SELECT IFNULL(SUM(amount), 0) FROM pension WHERE user_id = user_id);

    -- Calculate the net worth for the user
    SET net_worth = total_savings + total_investments + total_pension;

    -- Check if a record already exists for the user and payday
    IF EXISTS (SELECT 1 FROM net_worth WHERE user_id = user_id AND payday_id = payday_id) THEN
        -- Update the existing record
        UPDATE net_worth
        SET total_savings = total_savings,
            total_investments = total_investments,
            total_pension = total_pension,
            net_worth = net_worth,
            date = CURRENT_TIMESTAMP
        WHERE user_id = user_id AND payday_id = payday_id;
    ELSE
        -- Insert a new record
        INSERT INTO net_worth (user_id, payday_id, date, total_savings, total_investments, total_pension, net_worth)
        VALUES (user_id, payday_id, CURRENT_TIMESTAMP, total_savings, total_investments, total_pension, net_worth);
    END IF;
END //

DELIMITER ;

-- These triggers will call the update_net_worth procedure whenever an insert or update operation occurs.
DELIMITER //

-- Trigger for savings table
CREATE TRIGGER update_net_worth_after_savings
AFTER INSERT OR UPDATE ON savings
FOR EACH ROW
BEGIN
    CALL update_net_worth(NEW.user_id, NEW.payday_id);
END //

-- Trigger for broker table
CREATE TRIGGER update_net_worth_after_broker
AFTER INSERT OR UPDATE ON broker
FOR EACH ROW
BEGIN
    CALL update_net_worth(NEW.user_id, NEW.payday_id);
END //

-- Trigger for pension table
CREATE TRIGGER update_net_worth_after_pension
AFTER INSERT OR UPDATE ON pension
FOR EACH ROW
BEGIN
    CALL update_net_worth(NEW.user_id, NEW.payday_id);
END //

-- Trigger for bank table
CREATE TRIGGER update_net_worth_after_bank
AFTER INSERT OR UPDATE ON bank
FOR EACH ROW
BEGIN
    CALL update_net_worth(NEW.user_id, NEW.payday_id);
END //

DELIMITER ;
