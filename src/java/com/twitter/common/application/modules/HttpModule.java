package com.twitter.common.application.modules;

import java.util.Set;
import java.util.logging.Logger;

import com.google.inject.AbstractModule;
import com.google.inject.Inject;
import com.google.inject.Injector;
import com.google.inject.Key;
import com.google.inject.Singleton;
import com.google.inject.TypeLiteral;
import com.google.inject.name.Names;
import com.google.inject.servlet.GuiceFilter;
import com.google.inject.servlet.GuiceServletContextListener;

import org.mortbay.jetty.RequestLog;

import com.twitter.common.application.ShutdownRegistry;
import com.twitter.common.application.http.DefaultQuitHandler;
import com.twitter.common.application.http.GraphViewer;
import com.twitter.common.application.http.HttpAssetConfig;
import com.twitter.common.application.http.HttpFilterConfig;
import com.twitter.common.application.http.HttpServletConfig;
import com.twitter.common.application.http.Registration;
import com.twitter.common.application.http.Registration.IndexLink;
import com.twitter.common.application.modules.LifecycleModule.ServiceRunner;
import com.twitter.common.application.modules.LocalServiceRegistry.LocalService;
import com.twitter.common.args.Arg;
import com.twitter.common.args.CmdLine;
import com.twitter.common.args.constraints.Range;
import com.twitter.common.base.Command;
import com.twitter.common.base.ExceptionalSupplier;
import com.twitter.common.base.Supplier;
import com.twitter.common.net.http.HttpServerDispatch;
import com.twitter.common.net.http.JettyHttpServerDispatch;
import com.twitter.common.net.http.RequestLogger;
import com.twitter.common.net.http.handlers.AbortHandler;
import com.twitter.common.net.http.handlers.ContentionPrinter;
import com.twitter.common.net.http.handlers.HealthHandler;
import com.twitter.common.net.http.handlers.LogConfig;
import com.twitter.common.net.http.handlers.LogPrinter;
import com.twitter.common.net.http.handlers.QuitHandler;
import com.twitter.common.net.http.handlers.StringTemplateServlet.CacheTemplates;
import com.twitter.common.net.http.handlers.ThreadStackPrinter;
import com.twitter.common.net.http.handlers.TimeSeriesDataSource;
import com.twitter.common.net.http.handlers.VarsHandler;
import com.twitter.common.net.http.handlers.VarsJsonHandler;
import com.twitter.common.net.http.handlers.pprof.CpuProfileHandler;

import static com.google.common.base.Preconditions.checkNotNull;

/**
 * Binding module for injections related to the HTTP server and the default set of servlets.
 *
 * This module uses a single command line argument 'http_port'.  If unset, the HTTP server will
 * be started on an ephemeral port.
 *
 * The default HTTP server includes several generic servlets that are useful for debugging.
 *
 * There are convenience methods in {@link Registration} to bind servlets and index links, but
 * {@link com.google.inject.servlet.ServletModule} may also be used for this purpose.
 *
 * Bindings provided by this module:
 * <ul>
 *   <li>{@code @CacheTemplates boolean} - True if parsed stringtemplates for servlets are cached.
 * </ul>
 *
 * Bindings that may be overridden with an override module:
 * <ul>
 *   <li>Abort handler: called when an HTTP GET request is issued to the /abortabortabort HTTP
 *       servlet.  May be overridden by binding to:
 *       {@code bind(Runnable.class).annotatedWith(Names.named(AbortHandler.ABORT_HANDLER_KEY))}.
 *   <li>Quit handler: called when an HTTP GET request is issued to the /quitquitquit HTTP
 *       servlet.  May be overridden by binding to:
 *       {@code bind(Runnable.class).annotatedWith(Names.named(QuitHandler.QUIT_HANDLER_KEY))}.
 *   <li>Health checker: called to determine whether the application is healthy to serve an
 *       HTTP GET request to /health.  May be overridden by binding to:
 *       {@code bind(new TypeLiteral<ExceptionalSupplier<Boolean, ?>>() {})
 *            .annotatedWith(Names.named(HealthHandler.HEALTH_CHECKER_KEY))}.
 *   <li>
 * </ul>
 */
public class HttpModule extends AbstractModule {

  @Range(lower = 0, upper = 65535)
  @CmdLine(name = "http_port",
           help = "The port to start an HTTP server on.  Default value will choose a random port.")
  protected static final Arg<Integer> HTTP_PORT = Arg.create(0);

  @CmdLine(name = "http_primary_service", help = "True if HTTP is the primary service.")
  protected static final Arg<Boolean> HTTP_PRIMARY_SERVICE = Arg.create(false);

  private static final Logger LOG = Logger.getLogger(HttpModule.class.getName());

  // TODO(William Farner): Consider making this configurable if needed.
  private static final boolean CACHE_TEMPLATES = true;

  private static final Runnable DEFAULT_ABORT_HANDLER = new Runnable() {
      @Override public void run() {
        LOG.info("ABORTING PROCESS IMMEDIATELY!");
        System.exit(0);
      }
    };
  private static final Supplier<Boolean> DEFAULT_HEALTH_CHECKER = new Supplier<Boolean>() {
      @Override public Boolean get() {
        return Boolean.TRUE;
      }
    };

  @Override
  protected void configure() {
    requireBinding(Injector.class);
    requireBinding(ShutdownRegistry.class);

    // Bind the default abort, quit, and health check handlers.
    bind(Key.get(Runnable.class, Names.named(AbortHandler.ABORT_HANDLER_KEY)))
        .toInstance(DEFAULT_ABORT_HANDLER);
    bind(Runnable.class).annotatedWith(Names.named(QuitHandler.QUIT_HANDLER_KEY))
        .to(DefaultQuitHandler.class);
    bind(DefaultQuitHandler.class).in(Singleton.class);
    bind(new TypeLiteral<ExceptionalSupplier<Boolean, ?>>() { })
        .annotatedWith(Names.named(HealthHandler.HEALTH_CHECKER_KEY))
        .toInstance(DEFAULT_HEALTH_CHECKER);

    // Allow template reloading in interactive mode for easy debugging of string templates.
    bindConstant().annotatedWith(CacheTemplates.class).to(CACHE_TEMPLATES);

    bind(HttpServerDispatch.class).to(JettyHttpServerDispatch.class)
        .in(Singleton.class);
    bind(RequestLog.class).to(RequestLogger.class);
    Registration.registerServlet(binder(),
        new HttpServletConfig("/abortabortabort", AbortHandler.class, true),
        new HttpServletConfig("/contention", ContentionPrinter.class, false),
        new HttpServletConfig("/graphdata", TimeSeriesDataSource.class, true),
        new HttpServletConfig("/health", HealthHandler.class, true),
        new HttpServletConfig("/logconfig", LogConfig.class, false),
        new HttpServletConfig("/logs", LogPrinter.class, false),
        new HttpServletConfig("/pprof/profile", CpuProfileHandler.class, false),
        new HttpServletConfig("/quitquitquit", QuitHandler.class, true),
        new HttpServletConfig("/threads", ThreadStackPrinter.class, false),
        new HttpServletConfig("/vars", VarsHandler.class, false),
        new HttpServletConfig("/vars.json", VarsJsonHandler.class, false));

    GraphViewer.registerResources(binder());

    LifecycleModule.bindServiceRunner(binder(), HttpServerLauncher.class);

    // Ensure at least an empty set of additional links is bound.
    Registration.getEndpointBinder(binder());
  }

  public static final class HttpServerLauncher implements ServiceRunner {
    private final HttpServerDispatch httpServer;
    private final Set<HttpAssetConfig> httpAssets;
    private final Set<HttpFilterConfig> httpFilters;
    private final Injector injector;
    private final Set<String> additionalIndexLinks;

    @Inject HttpServerLauncher(
        HttpServerDispatch httpServer,
        Set<HttpAssetConfig> httpAssets,
        Set<HttpFilterConfig> httpFilters,
        @IndexLink Set<String> additionalIndexLinks,
        Injector injector) {

      this.httpServer = checkNotNull(httpServer);
      this.httpAssets = checkNotNull(httpAssets);
      this.httpFilters = checkNotNull(httpFilters);
      this.additionalIndexLinks = checkNotNull(additionalIndexLinks);
      this.injector = checkNotNull(injector);
    }

    @Override public LocalService launch() {
      if (!httpServer.listen(HTTP_PORT.get())) {
        throw new IllegalStateException("Failed to start HTTP server, all servlets disabled.");
      }

      httpServer.registerListener(new GuiceServletContextListener() {
        @Override protected Injector getInjector() {
          return injector;
        }
      });
      httpServer.registerFilter(GuiceFilter.class, "/*");

      for (HttpAssetConfig config : httpAssets) {
        httpServer.registerHandler(config.path, config.handler, null, config.silent);
      }

      for (HttpFilterConfig filter : httpFilters) {
        httpServer.registerFilter(filter.filterClass, filter.pathSpec);
      }

      for (String indexLink : additionalIndexLinks) {
        httpServer.registerIndexLink(indexLink);
      }

      Command shutdown = new Command() {
        @Override public void execute() {
          LOG.info("Shutting down embedded http server");
          httpServer.stop();
        }
      };

      return HTTP_PRIMARY_SERVICE.get()
          ? LocalService.primaryService(httpServer.getPort(), shutdown)
          : LocalService.auxiliaryService("http", httpServer.getPort(), shutdown);
    }
  }
}
