-- Harden the persistence layer for payment requests, payments and transactions.
-- Note: Existing zero/negative production rows need controlled review BEFORE applying.
-- Prisma 6 does not support native @@check annotations; keep rules in SQL migrations.

ALTER TABLE "payment_requests"
    ADD CONSTRAINT "payment_requests_amount_positive_check"
    CHECK ("amount" > 0);

ALTER TABLE "payments"
    ADD CONSTRAINT "payments_amount_positive_check"
    CHECK ("amount" > 0);

ALTER TABLE "transactions"
    ADD CONSTRAINT "transactions_amount_positive_check"
    CHECK ("amount" > 0);
