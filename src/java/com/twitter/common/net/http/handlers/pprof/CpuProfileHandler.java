package com.twitter.common.net.http.handlers.pprof;

import java.io.IOException;
import java.io.OutputStream;
import java.util.logging.Logger;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.google.common.io.Closeables;

import com.twitter.common.quantity.Amount;
import com.twitter.common.quantity.Time;
import com.twitter.jvm.CpuProfile;
import com.twitter.util.Duration;

/**
 * A handler that collects CPU profile information for the running application and replies
 * in a format recognizable by gperftools: http://code.google.com/p/gperftools
 */
public class CpuProfileHandler extends HttpServlet {

  private static final Logger LOG = Logger.getLogger(CpuProfileHandler.class.getName());

  private int getParam(HttpServletRequest request, String param, int defaultValue) {
    String value = request.getParameter(param);
    int result = defaultValue;
    if (value != null) {
      try {
        result = Integer.parseInt(value);
      } catch (NumberFormatException e) {
        LOG.warning("Invalid integer for parameter " + param);
      }
    }
    return result;
  }

  @Override
  protected void doGet(HttpServletRequest req, HttpServletResponse resp)
      throws ServletException, IOException {
    int profileDurationSecs = getParam(req, "seconds", 10);
    int profilePollRate = getParam(req, "hz", 100);
    LOG.info("Collecting CPU profile for " + profileDurationSecs + " seconds at "
        + profilePollRate + " Hz");
    Duration sampleDuration =
        new Duration(Amount.of(profileDurationSecs, Time.SECONDS).as(Time.NANOSECONDS));
    CpuProfile profile =
        CpuProfile.recordInThread(sampleDuration, profilePollRate, Thread.State.RUNNABLE).get();
    resp.setHeader("Content-Type", "pprof/raw");
    resp.setStatus(HttpServletResponse.SC_OK);
    OutputStream responseBody = resp.getOutputStream();
    try {
      profile.writeGoogleProfile(resp.getOutputStream());
    } finally {
      Closeables.closeQuietly(responseBody);
    }
  }
}
