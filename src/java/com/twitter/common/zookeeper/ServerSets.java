package com.twitter.common.zookeeper;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.Map;
import java.util.Set;

import com.google.common.base.Preconditions;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterables;

import com.twitter.common.base.MorePreconditions;
import com.twitter.common.io.Codec;
import com.twitter.thrift.Endpoint;
import com.twitter.thrift.ServiceInstance;
import com.twitter.thrift.Status;

/**
 * Common ServerSet related functions
 */
public class ServerSets {

  private ServerSets() {
    // Utility class.
  }

  /**
   * Creates a server set that registers at a single path.
   *
   * @param zkClient ZooKeeper client to register with.
   * @param zkPath Path to register at.
   * @see #create(ZooKeeperClient, java.util.Set)
   * @return A server set that registers at {@code zkPath}.
   */
  public static ServerSet create(ZooKeeperClient zkClient, String zkPath) {
    return create(zkClient, ImmutableSet.of(zkPath));
  }

  /**
   * Creates a server set that registers at one or multiple paths.
   *
   * @param zkClient ZooKeeper client to register with.
   * @param zkPaths Paths to register at, must be non-empty.
   * @return A server set that registers at the given {@code zkPath}s.
   */
  public static ServerSet create(ZooKeeperClient zkClient, Set<String> zkPaths) {
    Preconditions.checkNotNull(zkClient);
    MorePreconditions.checkNotBlank(zkPaths);

    if (zkPaths.size() == 1) {
      return new ServerSetImpl(zkClient, Iterables.getOnlyElement(zkPaths));
    } else {
      ImmutableList.Builder<ServerSet> builder = ImmutableList.builder();
      for (String path : zkPaths) {
        builder.add(new ServerSetImpl(zkClient, path));
      }
      return new CompoundServerSet(builder.build());
    }
  }

  /**
   * Returns a serialized Thrift service instance object, with given endpoints and codec.
   *
   * @param serviceInstance the Thrift service instance object to be serialized
   * @param codec the codec to use to serialize a Thrift service instance object
   * @return byte array that contains a serialized Thrift service instance
   */
  public static byte[] serializeServiceInstance(
      ServiceInstance serviceInstance, Codec<ServiceInstance> codec) throws IOException {

    ByteArrayOutputStream output = new ByteArrayOutputStream();
    codec.serialize(serviceInstance, output);
    return output.toByteArray();
  }

  /**
   * Serializes a service instance based on endpoints.
   * @see #serializeServiceInstance(ServiceInstance, Codec)
   *
   * @param address the target address of the service instance
   * @param additionalEndpoints additional endpoints of the service instance
   * @param status service status
   */
  public static byte[] serializeServiceInstance(
      InetSocketAddress address,
      Map<String, Endpoint> additionalEndpoints,
      Status status,
      Codec<ServiceInstance> codec) throws IOException {

    ServiceInstance serviceInstance =
        new ServiceInstance(toEndpoint(address), additionalEndpoints, status);
    return serializeServiceInstance(serviceInstance, codec);
  }

  /**
   * Creates a service instance object deserialized from byte array.
   *
   * @param data the byte array contains a serialized Thrift service instance
   * @param codec the codec to use to deserialize the byte array
   */
  public static ServiceInstance deserializeServiceInstance(
      byte[] data, Codec<ServiceInstance> codec) throws IOException {

    return codec.deserialize(new ByteArrayInputStream(data));
  }

  /**
   * Creates an endpoint for the given InetSocketAddress.
   *
   * @param address the target address to create the endpoint for
   */
  public static Endpoint toEndpoint(InetSocketAddress address) {
    return new Endpoint(address.getHostName(), address.getPort());
  }
}
