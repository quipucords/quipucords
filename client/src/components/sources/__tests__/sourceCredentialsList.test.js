import React from 'react';
import { mount } from 'enzyme';
import SourceCredentialsList from '../sourceCredentialsList';

describe('SourceCredentialsList Component', () => {
  it('should render a sorted list', () => {
    const props = {
      source: {
        credentials: [
          {
            name: 'a test'
          },
          {
            name: 'b test'
          }
        ]
      }
    };

    const component = mount(<SourceCredentialsList {...props} />);

    expect(component.render()).toMatchSnapshot();
  });
});
