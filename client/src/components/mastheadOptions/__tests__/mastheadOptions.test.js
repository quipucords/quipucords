import React from 'react';
import { mount } from 'enzyme';
import MastheadOptions from '../mastheadOptions';

describe('MastheadOptions Component', () => {
  it('should render', () => {
    const props = {
      user: { currentUser: { username: 'Admin' } }
    };

    const component = mount(<MastheadOptions {...props} />);

    expect(component.render()).toMatchSnapshot();
  });
});
