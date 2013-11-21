// =================================================================================================
// Copyright 2013 Twitter, Inc.
// -------------------------------------------------------------------------------------------------
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this work except in compliance with the License.
// You may obtain a copy of the License in the LICENSE file, or at:
//
//  http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// =================================================================================================

package com.twitter.common.metrics;

/**
 * A registry that maintains a collection of metrics.
 */
public interface MetricRegistry {

  /**
   * Returns or creates a sub-scope of this metric registry.
   *
   * @param name Name for the sub-scope.
   * @return A possibly-new metric registry, whose metrics will be 'children' of this scope.
   */
  MetricRegistry scope(String name);

  /**
   * Registers a new gauge.
   *
   * @param gauge Gauge to register.
   * @param <T> Number type of the gauge's values.
   */
  <T extends Number> void register(Gauge<T> gauge);

  /**
   * Creates a gauge and returns an {@link Counter} that can be incremented.
   *
   * @param name Name to associate with the gauge.
   * @return Counter (initialized to zero) to increment the value.
   */
  Counter createCounter(String name);
}
