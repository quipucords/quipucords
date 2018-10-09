import React from 'react';
import { mount } from 'enzyme';
import About from '../about';

describe('About Component', () => {
  it('should render a basic display', () => {
    const props = {
      user: { currentUser: { username: 'admin' } },
      status: {},
      shown: true,
      onClose: jest.fn()
    };

    const component = mount(<About {...props} />);

    expect(component.render()).toMatchSnapshot();
  });
});
