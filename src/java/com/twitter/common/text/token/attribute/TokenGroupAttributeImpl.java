// =================================================================================================
// Copyright 2011 Twitter, Inc.
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

package com.twitter.common.text.token.attribute;

import java.io.IOException;
import java.io.NotSerializableException;
import java.io.ObjectStreamException;
import java.util.Collections;
import java.util.List;

import com.google.common.collect.Lists;

import org.apache.lucene.util.AttributeImpl;
import org.apache.lucene.util.AttributeSource;

import com.twitter.common.text.token.TokenGroupStream;
import com.twitter.common.text.token.TokenizedCharSequence;
import com.twitter.common.text.token.TokenizedCharSequenceStream;

/**
 * Implementation of {@link TokenGroupAttribute}.
 * <p>
 * Note that this class explicitly suppresses the ability for instance to be serialized, inherited
 * via {@link AttributeImpl}.
 */
public class TokenGroupAttributeImpl extends AttributeImpl implements TokenGroupAttribute {
  private static final long serialVersionUID = 0L;

  private List<AttributeSource.State> states = Collections.emptyList();
  private AttributeSource attributeSource = null;
  private TokenizedCharSequence seq = null;

  @Override
  public void clear() {
    states = Collections.emptyList();
    seq = null;
  }

  @Override
  public void copyTo(AttributeImpl obj) {
    if (obj instanceof TokenGroupAttributeImpl) {
      TokenGroupAttributeImpl attr = (TokenGroupAttributeImpl) obj;
      attr.attributeSource = this.attributeSource;
      attr.states = Lists.newArrayList(this.states);
      attr.seq = this.seq;
    }
  }

  @Override
  public boolean equals(Object obj) {
    return (obj instanceof TokenGroupAttributeImpl)
      && (((TokenGroupAttributeImpl) obj).states.equals(states) &&
          ((TokenGroupAttributeImpl) obj).seq == null && seq == null) ||
         (((TokenGroupAttributeImpl) obj).seq != null && seq != null &&
            ((TokenGroupAttributeImpl) obj).seq.equals(seq));
  }

  @Override
  public int hashCode() {
    return (seq == null ? states.hashCode() : seq.hashCode());
  }

  @Override
  public boolean isEmpty() {
    return states.isEmpty() && (seq == null || seq.getTokens().isEmpty());
  }

  @Override
  public int size() {
    return (!states.isEmpty() ? states.size() :
        (seq != null ? seq.getTokens().size() : states.size()));
  }

  /**
   * Sets the list of states for this group. Invalidates any previously set sequence.
   */
  public void setStates(List<AttributeSource.State> states) {
    this.states = states;
    this.seq = null;
  }

  /**
   * Sets the attribute source for this group. Invalidates any previously set sequence.
   */
  public void setAttributeSource(AttributeSource source) {
    this.attributeSource = source;
    this.seq = null;
  }

  /**
   * Sets the group token stream as a sequence. Constructs a stream from this sequence lazily.
   * Invalidates any information set from setStates or setAttributeSource
   */
  public void setSequence(TokenizedCharSequence seq) {
    this.seq = seq;
    this.states = Collections.emptyList();
    this.attributeSource = null;
  }

  /**
   * Returns the backing TokenizedCharSequence. Will be null if group was set using states
   */
  public TokenizedCharSequence getSequence() {
    return seq;
  }

  @Override
  public TokenGroupStream getTokenGroupStream() {
    //Lazily process the sequence into a set of states, only do it when getTokenGroupStream is called
    if ((attributeSource == null || states.isEmpty()) && seq != null) {
      TokenizedCharSequenceStream ret = new TokenizedCharSequenceStream();
      ret.reset(seq);

      //TODO(alewis) This could probably be lazier. Make a new extension of TokenGroupStream?
      List<AttributeSource.State> states = Lists.newLinkedList();
      while (ret.incrementToken()) {
        states.add(ret.captureState());
      }
      setAttributeSource(ret.cloneAttributes());
      setStates(states);
    }
    return new TokenGroupStream(attributeSource, states);
  }

  // Explicitly suppress ability to serialize.
  private void writeObject(java.io.ObjectOutputStream out) throws IOException {
    throw new NotSerializableException();
  }

  private void readObject(java.io.ObjectInputStream in)
      throws IOException, ClassNotFoundException {
    throw new NotSerializableException();
  }

  private void readObjectNoData() throws ObjectStreamException {
    throw new NotSerializableException();
  }
}
