package com.twitter.common.testing.runner;

import org.junit.internal.requests.ClassRequest;

/**
 * Wrapper of ClassRequest that exposes the class.
 *
 * @author: Qicheng Ma
 */
public class AnnotatedClassRequest extends ClassRequest {
  private final Class clazz;

  public AnnotatedClassRequest(Class clazz) {
    super(clazz);
    this.clazz = clazz;
  }

  public Class getClazz() {
    return clazz;
  }
}
