import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import { Grid, Icon } from 'patternfly-react';
import { helpers } from '../../common/helpers';

class ScanSourceList extends React.Component {
  constructor() {
    super();

    this.state = {
      sources: []
    };
  }

  componentDidMount() {
    const { scan } = this.props;
    let sources = [...scan.sources];

    sources.sort((item1, item2) => {
      let cmp = item1.source_type.localeCompare(item2.source_type);
      if (cmp === 0) {
        cmp = item1.name.localeCompare(item2.name);
      }
      return cmp;
    });
    this.setState({ sources: sources });
  }

  componentWillReceiveProps(nextProps) {
    if (!_.isEqual(_.get(nextProps, 'scan'), _.get(this.props, 'scan'))) {
      const { scan } = this.nextProps;
      let sources = [...scan.sources];

      sources.sort((item1, item2) => {
        let cmp = item1.source_type.localeCompare(item2.source_type);
        if (cmp === 0) {
          cmp = item1.name.localeCompare(item2.name);
        }
        return cmp;
      });
      this.setState({ sources: sources });
    }
  }

  renderSourceIcon(source) {
    let iconInfo = helpers.sourceTypeIcon(source.source_type);

    return <Icon type={iconInfo.type} name={iconInfo.name} />;
  }

  render() {
    const { sources } = this.state;

    return (
      <Grid fluid>
        {sources.map((item, index) => (
          <Grid.Row key={index}>
            <Grid.Col xs={12} sm={4}>
              <span>
                {this.renderSourceIcon(item)}
                &nbsp; {item.name}
              </span>
            </Grid.Col>
          </Grid.Row>
        ))}
      </Grid>
    );
  }
}

ScanSourceList.propTypes = {
  scan: PropTypes.object
};

export { ScanSourceList };
