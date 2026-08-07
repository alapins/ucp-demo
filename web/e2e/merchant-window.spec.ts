import { expect, test, type Page } from "@playwright/test";

/**
 * A Merchant operator raising Invoices and watching what the system of record says
 * back. Each test raises its own Invoice against a Payer nobody else uses, so it can
 * find its own row in a list every other test is also adding to.
 */

const aPayerOfItsOwn = () =>
  `raised-${Date.now()}-${Math.floor(Math.random() * 1000)}@example.com`;

async function raiseInvoice(
  page: Page,
  invoice: { payerEmail: string; amount: string; dueDate?: string },
) {
  await page.getByLabel("Payer email").fill(invoice.payerEmail);
  await page.getByLabel("Amount").fill(invoice.amount);
  if (invoice.dueDate) {
    await page.getByLabel("Due date").fill(invoice.dueDate);
  }
  await page.getByRole("button", { name: "Raise Invoice" }).click();
}

const rowFor = (page: Page, payerEmail: string) =>
  page.getByTestId("invoice-list").locator("tr", { hasText: payerEmail });

test.beforeEach(async ({ page }) => {
  await page.goto("/merchant");
  await expect(page.locator(".connection")).toHaveText("live");
});

test("the due date is offered thirty days out", async ({ page }) => {
  const inThirtyDays = new Date();
  inThirtyDays.setDate(inThirtyDays.getDate() + 30);

  await expect(page.getByLabel("Due date")).toHaveValue(
    inThirtyDays.toISOString().slice(0, 10),
  );
});

test("a raised Invoice reaches the list by way of the event stream", async ({
  page,
}) => {
  const payerEmail = aPayerOfItsOwn();
  const announcements = page
    .getByTestId("event-log")
    .locator("li", { hasText: "invoice.created" });
  const announcedBefore = await announcements.count();

  await raiseInvoice(page, { payerEmail, amount: "430.00", dueDate: "2099-03-28" });

  // The list is only ever reloaded when the Event Bus says an Invoice changed, so a
  // row appearing here is proof the creation event reached this window.
  const raised = rowFor(page, payerEmail);
  await expect(raised).toHaveCount(1);
  await expect(raised).toContainText("2099-03-28");
  await expect(raised).toContainText("$430.00");
  await expect(raised).toContainText("Outstanding");
  await expect(announcements).toHaveCount(announcedBefore + 1);

  // Opaque, and not the row number it happens to occupy.
  const docNumber = await raised.locator(".doc-number").innerText();
  expect(docNumber).not.toEqual("");
  expect(docNumber).not.toEqual(String(await rowFor(page, "@example.com").count()));
});

test("an Invoice raised outside this browser still lands in the list", async ({
  page,
  request,
}) => {
  // Nothing in the window asked for this Invoice, so the only way it can appear is
  // the Event Bus telling the window that the Merchant's records changed. This is
  // also how the Agent's payments will show up here.
  const payerEmail = aPayerOfItsOwn();

  await request.post("http://localhost:8080/invoices", {
    data: { payerEmail, originalTotalMinorUnits: 100000, dueDate: "2099-03-28" },
  });

  await expect(rowFor(page, payerEmail)).toHaveCount(1);
  await expect(rowFor(page, payerEmail)).toContainText("$1,000.00");
});

test("an Invoice whose due date has passed is listed as Overdue", async ({
  page,
}) => {
  const payerEmail = aPayerOfItsOwn();

  await raiseInvoice(page, { payerEmail, amount: "200.60", dueDate: "2019-03-28" });

  await expect(rowFor(page, payerEmail)).toContainText("Overdue");
});
