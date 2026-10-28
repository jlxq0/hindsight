import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { once } from "node:events";
import { createServer } from "node:net";
import { fileURLToPath } from "node:url";
import { test } from "node:test";

// next dev and a mocked intl middleware miss this standalone bind-host regression.
test(
  "standalone locale routing retains authentication on a non-localhost bind",
  { timeout: 30000 },
  async () => {
    const reservation = createServer();
    reservation.listen(0, "127.0.0.1");
    await once(reservation, "listening");
    const port = reservation.address().port;
    await new Promise((resolve) => reservation.close(resolve));
    const origin = `http://127.0.0.1:${port}`;
    const key = "synthetic-" + randomUUID();
    const server = spawn(process.execPath, ["server.js"], {
      cwd: fileURLToPath(new URL("../standalone/", import.meta.url)),
      env: {
        NODE_ENV: "production",
        HOSTNAME: "127.0.0.1",
        PORT: String(port),
        HINDSIGHT_CP_ACCESS_KEY: key,
        HINDSIGHT_CP_DATAPLANE_API_URL: "http://127.0.0.1:1",
      },
      stdio: ["ignore", "pipe", "pipe"],
    });
    let logs = "";
    const collect = (chunk) => {
      logs = (logs + chunk.toString()).slice(-8192);
    };
    server.stdout.on("data", collect);
    server.stderr.on("data", collect);
    const exit = once(server, "exit");
    const request = (path, options = {}) =>
      fetch(origin + path, {
        redirect: "manual",
        signal: AbortSignal.timeout(4000),
        ...options,
      });
    const login = (candidate) =>
      request("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: candidate }),
      });
    let failure;
    try {
      const deadline = Date.now() + 10000;
      while (true) {
        assert.equal(server.exitCode, null, `Standalone exited: ${logs}`);
        try {
          if ((await request("/api/auth/login")).status === 405) break;
        } catch {
          /* The server may still be opening its listener. */
        }
        assert.ok(Date.now() < deadline, `Standalone readiness timeout: ${logs}`);
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
      const anonymous = await request("/dashboard");
      assert.equal(anonymous.status, 307);
      assert.equal(new URL(anonymous.headers.get("location"), origin).pathname, "/login");
      assert.equal((await request("/api/banks")).status, 401);
      for (const locale of ["en", "de", "zh-CN"]) {
        const page = await request("/login", { headers: { "Accept-Language": locale } });
        assert.equal(page.status, 200, `${locale} login must render without a loop`);
        assert.match(await page.text(), /Hindsight/);
      }
      const invalid = await login("incorrect");
      assert.equal(invalid.status, 401);
      assert.equal(invalid.headers.get("set-cookie"), null);
      const authenticated = await login(key);
      assert.equal(authenticated.status, 200);
      const setCookie = authenticated.headers
        .getSetCookie()
        .find((value) => value.startsWith("hindsight_cp_access="));
      assert.match(setCookie, /HttpOnly/i);
      const headers = { cookie: setCookie.split(";")[0] };
      const home = await request("/", { headers });
      assert.equal(home.status, 307);
      assert.equal(new URL(home.headers.get("location"), origin).href, origin + "/dashboard");
      const dashboard = await request("/dashboard", { headers });
      assert.equal(dashboard.status, 200);
      assert.match(dashboard.headers.get("content-type"), /text\/html/);
      assert.match(await dashboard.text(), /Hindsight/);
      const canonical = await request("/en/dashboard", { headers });
      assert.equal(canonical.status, 307);
      assert.equal(new URL(canonical.headers.get("location"), origin).pathname, "/dashboard");
      const escape = await request("/login?returnTo=%2F%2Fexample.com", { headers });
      assert.equal(new URL(escape.headers.get("location"), origin).href, origin + "/dashboard");
      const logout = await request("/api/auth/logout", { method: "POST", headers });
      assert.equal(logout.status, 200);
      assert.match(logout.headers.get("set-cookie"), /Max-Age=0/i);
      // Clearing the client cookie is not server-side token revocation.
      assert.equal((await request("/api/banks")).status, 401);
    } catch (error) {
      console.error(logs);
      failure = error;
    } finally {
      if (server.exitCode === null && server.signalCode === null) server.kill("SIGTERM");
      let timer;
      try {
        await Promise.race([
          exit,
          new Promise((_, reject) => {
            timer = setTimeout(() => reject(new Error("Standalone did not stop")), 3000);
          }),
        ]);
      } catch (error) {
        server.kill("SIGKILL");
        await exit;
        failure = failure
          ? new AggregateError([failure, error], "Routing and cleanup failed")
          : error;
      } finally {
        clearTimeout(timer);
      }
    }
    if (failure) throw failure;
  }
);
