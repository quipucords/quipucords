import _ from 'lodash';
import React from 'react';
import { connect } from 'react-redux';
import cx from 'classnames';
import PropTypes from 'prop-types';
import { ListView, Button, Grid, Icon, Checkbox } from 'patternfly-react';
import { helpers } from '../../common/helpers';
import SimpleTooltip from '../simpleTooltIp/simpleTooltip';
import Store from '../../redux/store';
import { viewTypes } from '../../redux/constants';

class CredentialListItem extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['itemSelectChange', 'toggleExpand', 'closeExpand']);
  }

  expandType() {
    const { item, expandedCredentials } = this.props;

    return _.get(
      _.find(expandedCredentials, nextExpanded => {
        return nextExpanded.id === item.id;
      }),
      'expandType'
    );
  }

  isSelected() {
    const { item, selectedCredentials } = this.props;

    return (
      _.find(selectedCredentials, nextSelected => {
        return nextSelected.id === item.id;
      }) !== undefined
    );
  }

  itemSelectChange() {
    const { item } = this.props;

    Store.dispatch({
      type: this.isSelected() ? viewTypes.DESELECT_ITEM : viewTypes.SELECT_ITEM,
      viewType: viewTypes.CREDENTIALS_VIEW,
      item: item
    });
  }

  toggleExpand(expandType) {
    const { item } = this.props;

    if (expandType === this.expandType()) {
      Store.dispatch({
        type: viewTypes.EXPAND_ITEM,
        viewType: viewTypes.CREDENTIALS_VIEW,
        item: item
      });
    } else {
      Store.dispatch({
        type: viewTypes.EXPAND_ITEM,
        viewType: viewTypes.CREDENTIALS_VIEW,
        item: item,
        expandType: expandType
      });
    }
  }

  closeExpand() {
    const { item } = this.props;
    Store.dispatch({
      type: viewTypes.EXPAND_ITEM,
      viewType: viewTypes.CREDENTIALS_VIEW,
      item: item
    });
  }

  renderActions() {
    const { item, onEdit, onDelete } = this.props;

    return [
      <SimpleTooltip key="editButton" id="editTip" tooltip="Edit Credential">
        <Button
          onClick={() => {
            onEdit(item);
          }}
          bsStyle="link"
          key="editButton"
        >
          <Icon type="pf" name="edit" />
        </Button>
      </SimpleTooltip>,
      <SimpleTooltip key="deleteButton" id="deleteTip" tooltip="Delete Credential">
        <Button
          onClick={() => {
            onDelete(item);
          }}
          bsStyle="link"
          key="removeButton"
        >
          <Icon type="pf" name="delete" />
        </Button>
      </SimpleTooltip>
    ];
  }

  renderStatusItems() {
    const { item } = this.props;

    let sourceCount = item.sources ? item.sources.length : 0;

    return [
      <ListView.InfoItem
        key="sources"
        className={'list-view-info-item-icon-count ' + (sourceCount === 0 ? 'invisible' : '')}
      >
        <ListView.Expand
          expanded={this.expandType() === 'sources'}
          toggleExpanded={() => {
            this.toggleExpand('sources');
          }}
        >
          <strong>{sourceCount}</strong>
          {sourceCount === 1 ? ' Source' : ' Sources'}
        </ListView.Expand>
      </ListView.InfoItem>
    ];
  }

  renderExpansionContents() {
    const { item, expandedCredentials } = this.props;
    const typeIcon = helpers.sourceTypeIcon(item.cred_type);

    switch (this.expandType(item, expandedCredentials)) {
      case 'sources':
        item.sources &&
          item.sources.sort((item1, item2) => {
            return item1.name.localeCompare(item2.name);
          });
        return (
          <Grid fluid>
            {item.sources &&
              item.sources.map((source, index) => {
                return (
                  <Grid.Row key={index}>
                    <Grid.Col xs={12} sm={4}>
                      <span>
                        <SimpleTooltip id="sourceTypeTip" tooltip={helpers.sourceTypeString(source.source_type)}>
                          <Icon type={typeIcon.type} name={typeIcon.name} />
                        </SimpleTooltip>
                        &nbsp; {source.name}
                      </span>
                    </Grid.Col>
                  </Grid.Row>
                );
              })}
          </Grid>
        );
      default:
        return null;
    }
  }

  render() {
    const { item } = this.props;
    const selected = this.isSelected();
    const sourceTypeIcon = helpers.sourceTypeIcon(item.cred_type);
    const classes = cx({
      'quipucords-credential-list-item': true,
      'list-view-pf-top-align': true,
      active: selected
    });

    return (
      <ListView.Item
        key={item.id}
        stacked
        className={classes}
        checkboxInput={<Checkbox checked={selected} bsClass="" onChange={this.itemSelectChange} />}
        actions={this.renderActions()}
        leftContent={
          <SimpleTooltip id="credentialTypeTip" tooltip={helpers.sourceTypeString(item.cred_type)}>
            <ListView.Icon type={sourceTypeIcon.type} name={sourceTypeIcon.name} />
          </SimpleTooltip>
        }
        description={
          <div className="quipucords-split-description">
            <span className="quipucords-description-left">
              <ListView.DescriptionHeading>{item.name}</ListView.DescriptionHeading>
            </span>
            <span className="quipucords-description-right">
              <SimpleTooltip id="methodTip" tooltip="Authorization Type">
                {helpers.authorizationTypeString(item.auth_type)}
              </SimpleTooltip>
            </span>
          </div>
        }
        additionalInfo={this.renderStatusItems()}
        compoundExpand
        compoundExpanded={this.expandType() !== undefined}
        onCloseCompoundExpand={this.closeExpand}
      >
        {this.renderExpansionContents()}
      </ListView.Item>
    );
  }
}

CredentialListItem.propTypes = {
  item: PropTypes.object,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func,
  selectedCredentials: PropTypes.array,
  expandedCredentials: PropTypes.array
};

const mapStateToProps = function(state) {
  return Object.assign({
    selectedCredentials: state.viewOptions[viewTypes.CREDENTIALS_VIEW].selectedItems,
    expandedCredentials: state.viewOptions[viewTypes.CREDENTIALS_VIEW].expandedItems
  });
};

export default connect(mapStateToProps)(CredentialListItem);
