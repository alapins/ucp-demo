import { expect, test, type Page } from "@playwright/test";

/**
 * The demo's whole cycle, in the two windows a human watches it in: an Invoice is
 * raised in the merchant window, the Agent is woken in the agent window, and the
 * Invoice comes back settled.
 *
 * Unlike the merchant-window tests, this one cannot invent a Payer of its own. The
 * Agent holds one API key and that key names one Payer, so the Invoice it is asked to
 * pay must be that Payer's — the Agent has no way to be shown anyone else's.
 */

const THE_PAYER_THE_AGENT_ACTS_FOR = "vampserv@gmail.com";

const rowFor = (page: Page, docNumber: string) =>
  page.getByTestId("invoice-list").locator("tr", { hasText: docNumber });

const logOf = (page: Page, type: string) =>
  page.getByTestId("event-log").locator("li", { hasText: type });

test("an Invoice raised in one window is discovered and paid from the other", async ({
  page,
  context,
  request,
}) => {
  const merchantWindow = page;
  await merchantWindow.goto("/merchant");
  await expect(merchantWindow.locator(".connection")).toHaveText("live");

  const agentWindow = await context.newPage();
  await agentWindow.goto("/agent");
  await expect(agentWindow.locator(".connection")).toHaveText("live");

  // Raised through the Invoice API rather than through the form, only so the test can
  // read back the Doc Number the Merchant minted and follow that one Invoice.
  const raised = await request.post("http://localhost:8080/invoices", {
    data: {
      payerEmail: THE_PAYER_THE_AGENT_ACTS_FOR,
      originalTotalMinorUnits: 43000,
      dueDate: "2099-03-28",
    },
  });
  const { docNumber } = await raised.json();

  await expect(rowFor(merchantWindow, docNumber)).toContainText("Outstanding");
  await expect(rowFor(merchantWindow, docNumber)).toContainText("$430.00");

  await agentWindow.getByRole("button", { name: "Run Agent Now" }).click();

  // What the Payer watches happen on their own machine.
  await expect(logOf(agentWindow, "agent.woke").first()).toBeVisible();
  await expect(logOf(agentWindow, "agent.invoices_discovered").first()).toBeVisible();
  await expect(logOf(agentWindow, "agent.decided").first()).toBeVisible();
  await expect(logOf(agentWindow, "agent.payment_completed").first()).toBeVisible();
  // The Agent confirmed against the Merchant's own records rather than trusting the
  // Checkout it had just completed.
  await expect(logOf(agentWindow, "agent.payment_verified").first()).toBeVisible();

  // And what the Merchant sees, arriving by the event stream exactly as a payment made
  // by hand would. Nothing in this window asked for it.
  await expect(rowFor(merchantWindow, docNumber)).toContainText("Paid");
  await expect(rowFor(merchantWindow, docNumber)).toContainText("$0.00");
});

test("the merchant window never sees the Agent's reasoning", async ({
  page,
  context,
}) => {
  const merchantWindow = page;
  await merchantWindow.goto("/merchant");
  await expect(merchantWindow.locator(".connection")).toHaveText("live");

  const agentWindow = await context.newPage();
  await agentWindow.goto("/agent");
  await agentWindow.getByRole("button", { name: "Run Agent Now" }).click();
  await expect(logOf(agentWindow, "agent.finished").first()).toBeVisible();

  // The trust boundary of ADR 0004: the Merchant is told its own Invoice was paid, and
  // is never told what the Payer's Agent thought about it.
  await expect(logOf(merchantWindow, "agent.")).toHaveCount(0);
  await expect(logOf(merchantWindow, "ucp.checkout_completed").first()).toBeVisible();
});
