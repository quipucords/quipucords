import React from 'react';
import { mount } from 'enzyme';
import SimpleTooltip from '../simpleTooltip';

describe('SimpleTooltip Component', () => {
  it('should render', () => {
    const props = {
      id: 'test'
    };

    const component = mount(<SimpleTooltip {...props}>Test tooltip</SimpleTooltip>);

    expect(component.render()).toMatchSnapshot();
  });
});
