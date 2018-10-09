import React from 'react';
import { mount } from 'enzyme';
import { MenuItem } from 'patternfly-react';
import DropdownSelect from '../dropdownSelect';

describe('DropdownSelect Component', () => {
  it('should render', () => {
    const props = {
      id: 'testing',
      title: 'test title'
    };

    const component = mount(
      <DropdownSelect {...props}>
        <MenuItem key="one">One</MenuItem>
      </DropdownSelect>
    );

    expect(component.render()).toMatchSnapshot();
  });
});
