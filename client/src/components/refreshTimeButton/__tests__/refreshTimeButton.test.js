import React from 'react';
import { mount } from 'enzyme';
import RefreshTimeButton from '../refreshTimeButton';

describe('RefreshTimeButton Component', function() {
  it('should render', () => {
    const props = {
      onRefresh: jest.fn()
    };

    const component = mount(<RefreshTimeButton {...props} />);

    expect(component.render()).toMatchSnapshot();
  });
});
