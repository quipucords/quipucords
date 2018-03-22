import React from 'react';
import { shallow } from 'enzyme';
import Content from '../content';

describe('ConfirmationModal Component', function() {
  it('should shallow render a basic component', () => {
    const wrapper = shallow(<Content />);

    expect(wrapper).toMatchSnapshot();
  });
});
