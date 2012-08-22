package com.twitter.common.application.http;

import java.lang.annotation.Retention;
import java.lang.annotation.Target;
import java.net.URL;
import java.util.Set;

import javax.servlet.http.HttpServlet;

import com.google.common.collect.ImmutableSet;
import com.google.common.io.Resources;
import com.google.inject.Binder;
import com.google.inject.BindingAnnotation;
import com.google.inject.Singleton;
import com.google.inject.multibindings.Multibinder;
import com.google.inject.servlet.ServletModule;

import com.twitter.common.net.http.handlers.AssetHandler;
import com.twitter.common.net.http.handlers.AssetHandler.StaticAsset;

import static java.lang.annotation.ElementType.FIELD;
import static java.lang.annotation.ElementType.METHOD;
import static java.lang.annotation.ElementType.PARAMETER;
import static java.lang.annotation.RetentionPolicy.RUNTIME;

/**
 * Utility class for registering HTTP servlets and assets.
 */
public final class Registration {

  private Registration() {
    // Utility class.
  }

  /**
   * Equivalent to
   * {@code registerServlet(binder, new HttpServletConfig(path, servletClass, silent))}.
   */
  public static void registerServlet(Binder binder, String path,
      Class<? extends HttpServlet> servletClass, boolean silent) {
    registerServlet(binder, new HttpServletConfig(path, servletClass, silent));
  }

  /**
   * Registers a binding for an {@link javax.servlet.http.HttpServlet} to be exported at a specified
   * path.
   *
   * @param binder a guice binder to register the handler with
   * @param config a servlet mounting specification
   * @param additional additional servlets to mount
   */
  public static void registerServlet(
      final Binder binder,
      HttpServletConfig config,
      HttpServletConfig... additional) {

    final Set<HttpServletConfig> servletConfigs =
        ImmutableSet.<HttpServletConfig>builder().add(config).add(additional).build();
    binder.install(new ServletModule() {
      @Override protected void configureServlets() {
        for (HttpServletConfig servletConfig : servletConfigs) {
          bind(servletConfig.handlerClass).in(Singleton.class);
          serve(servletConfig.path).with(servletConfig.handlerClass);
          if (!servletConfig.silent) {
            registerEndpoint(binder, servletConfig.path);
          }
        }
      }
    });
  }

  /**
   * A binding annotation applied to the set of additional index page links bound via
   * {@link #Registration#registerEndpoint()}
   */
  @BindingAnnotation
  @Target({FIELD, PARAMETER, METHOD})
  @Retention(RUNTIME)
  public @interface IndexLink { }

  /**
   * Gets the multibinder used to bind links on the root servlet.
   * The resulting {@link java.util.Set} is bound with the {@link IndexLink} annotation.
   *
   * @param binder a guice binder to associate the multibinder with.
   * @return The multibinder to bind index links against.
   */
  public static Multibinder<String> getEndpointBinder(Binder binder) {
    return Multibinder.newSetBinder(binder, String.class, IndexLink.class);
  }

  /**
   * Registers a link to display on the root servlet.
   *
   * @param binder a guice binder to register the link with.
   * @param endpoint Endpoint URI to include.
   * @param additional additional endpoints to include.
   */
  public static void registerEndpoint(Binder binder, String endpoint, String... additional) {
    Multibinder<String> linkBinder = getEndpointBinder(binder);
    for (String link : ImmutableSet.<String>builder().add(endpoint).add(additional).build()) {
      linkBinder.addBinding().toInstance(link);
    }
  }

  /**
   * Registers a binding for a URL asset to be served by the HTTP server, with an optional
   * entity tag for cache control.
   *
   * @param binder a guice binder to register the handler with
   * @param servedPath Path to serve the resource from in the HTTP server.
   * @param asset Resource to be served.
   * @param assetType MIME-type for the asset.
   * @param silent Whether the server should hide this asset on the index page.
   */
  public static void registerHttpAsset(
      final Binder binder,
      final String servedPath,
      final URL asset,
      final String assetType,
      final boolean silent) {

    binder.install(new ServletModule() {
      @Override protected void configureServlets() {
        serve(servedPath).with(new AssetHandler(
            new StaticAsset(Resources.newInputStreamSupplier(asset), assetType, true)));
        if (!silent) {
          registerEndpoint(binder, servedPath);
        }
      }
    });
  }

  /**
   * Registers a binding for a classpath resource to be served by the HTTP server, using a resource
   * path relative to a class.
   *
   * @param binder a guice binder to register the handler with
   * @param servedPath Path to serve the asset from in the HTTP server.
   * @param contextClass Context class for defining the relative path to the asset.
   * @param assetRelativePath Path to the served asset, relative to {@code contextClass}.
   * @param assetType MIME-type for the asset.
   * @param silent Whether the server should hide this asset on the index page.
   */
  public static void registerHttpAsset(
      Binder binder,
      String servedPath,
      Class<?> contextClass,
      String assetRelativePath,
      String assetType,
      boolean silent) {

    registerHttpAsset(binder, servedPath, Resources.getResource(contextClass, assetRelativePath),
        assetType, silent);
  }
}
