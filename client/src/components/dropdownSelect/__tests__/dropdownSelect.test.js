import React from 'react';
import { mount } from 'enzyme';
import { MenuItem } from 'patternfly-react';
import DropdownSelect from '../dropdownSelect';

describe('DropdownSelect Component', () => {
  it('should render a basic component', () => {
    const props = {
      id: 'test',
      options: [{ title: 'lorem', value: 'ipsum' }, { title: 'hello', value: 'world', selected: true }]
    };

    let component = mount(
      <DropdownSelect {...props}>
        <MenuItem eventKey="ipsum">Lorem ipsum</MenuItem>
      </DropdownSelect>
    );

    expect(component.render()).toMatchSnapshot('basic dropdown');

    props.selectValue = ['world', 'ipsum'];
    props.multiselect = true;

    component = mount(
      <DropdownSelect {...props}>
        <MenuItem eventKey="ipsum">Lorem ipsum</MenuItem>
      </DropdownSelect>
    );

    expect(component.render()).toMatchSnapshot('multiselect dropdown');
  });

  it('should allow a alternate array and object options', () => {
    const props = {
      id: 'test',
      options: ['lorem', 'ipsum', 'hello', 'world'],
      selectValue: ['ipsum']
    };

    let component = mount(
      <DropdownSelect {...props}>
        <MenuItem eventKey="ipsum">Lorem ipsum</MenuItem>
      </DropdownSelect>
    );

    expect(component.render()).toMatchSnapshot('string array');

    props.options = { lorem: 'ipsum', hello: 'world' };

    component = mount(
      <DropdownSelect {...props}>
        <MenuItem eventKey="ipsum">Lorem ipsum</MenuItem>
      </DropdownSelect>
    );

    expect(component.render()).toMatchSnapshot('key value object');
  });

  it('should return an emulated onchange event', done => {
    const props = {
      id: 'test',
      options: ['lorem', 'ipsum', 'hello', 'world'],
      selectValue: ['ipsum']
    };

    props.onSelect = event => {
      expect(event).toMatchSnapshot('emulated event');
      done();
    };

    let component = mount(
      <DropdownSelect {...props}>
        <MenuItem eventKey="ipsum">Lorem ipsum</MenuItem>
      </DropdownSelect>
    );

    const componentInstance = component.instance();
    componentInstance.onSelect('hello');

    expect(component.render()).toMatchSnapshot('string array');

    props.options = { lorem: 'ipsum', hello: 'world' };

    component = mount(
      <DropdownSelect {...props}>
        <MenuItem eventKey="ipsum">Lorem ipsum</MenuItem>
      </DropdownSelect>
    );

    expect(component.render()).toMatchSnapshot('key value object');
  });
});
